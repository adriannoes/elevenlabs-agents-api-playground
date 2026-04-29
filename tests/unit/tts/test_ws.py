"""Unit tests for WebSocket TTS input streaming."""

from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest

from eleven_demo.tts import ws as ws_module
from eleven_demo.tts.ws import ws_stream


class _AsyncListIter:
    """Minimal async iterator wrapping a synchronous list."""

    def __init__(self, items: list[str]) -> None:
        self._it = iter(items)

    async def __anext__(self) -> str:
        try:
            await asyncio.sleep(0)
            return next(self._it)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    def __aiter__(self) -> _AsyncListIter:
        return self


class _FakeWs:
    """Fake WebSocket exposing send(...) and async iteration over canned messages."""

    def __init__(self, incoming: list[str]) -> None:
        self.sent: list[str] = []
        self._incoming = incoming

    async def send(self, data: str) -> None:
        self.sent.append(data)

    def __aiter__(self) -> _AsyncListIter:
        return _AsyncListIter(self._incoming)


class _AsyncConnectCm:
    """Async context manager that yields one fake websocket."""

    def __init__(self, websocket: _FakeWs) -> None:
        self._websocket = websocket

    async def __aenter__(self) -> _FakeWs:
        return self._websocket

    async def __aexit__(
        self,
        exc_type: object,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        return None


@pytest.mark.asyncio
async def test_ws_stream_streams_text_and_yields_audio_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeWs(
        incoming=[
            json.dumps({"audio": base64.b64encode(b"H").decode(), "isFinal": False}),
            json.dumps({"audio": base64.b64encode(b"i").decode(), "isFinal": True}),
        ],
    )

    captured: dict[str, str] = {"uri": ""}

    def fake_connect(uri: str, **kwargs: object) -> _AsyncConnectCm:
        captured["uri"] = uri
        assert kwargs["additional_headers"]["xi-api-key"] == "key"
        return _AsyncConnectCm(fake)

    monkeypatch.setattr(ws_module.websockets, "connect", fake_connect)

    mock_settings = MagicMock()
    mock_settings.elevenlabs_api_key.get_secret_value.return_value = "key"
    monkeypatch.setattr(ws_module, "get_settings", lambda: mock_settings)

    async def chunks() -> AsyncIterator[str]:
        yield "Hi"
        yield "there"

    out = [
        b
        async for b in ws_stream(
            chunks(),
            voice_id="vid",
            model_id="m1",
            output_format="pcm_44100",
        )
    ]
    assert out == [b"H", b"i"]

    assert captured["uri"].startswith(
        "wss://api.elevenlabs.io/v1/text-to-speech/vid/stream-input?",
    )
    assert "model_id=m1" in captured["uri"] and "output_format=pcm_44100" in captured["uri"]

    payloads = [json.loads(s) for s in fake.sent]
    assert payloads[0] == {"text": " "}
    assert payloads[-1] == {"text": ""}
    trigger_payloads = [p for p in payloads[1:-1] if "try_trigger_generation" in p]
    assert len(trigger_payloads) == 2
    assert trigger_payloads[0]["text"] == "Hi "
    assert trigger_payloads[1]["text"] == "there "
    assert all(p["try_trigger_generation"] for p in trigger_payloads)


@pytest.mark.asyncio
async def test_ws_stream_handles_empty_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeWs(incoming=[json.dumps({"audio": "", "isFinal": True})])

    monkeypatch.setattr(ws_module.websockets, "connect", lambda *_a, **_k: _AsyncConnectCm(fake))

    mock_settings = MagicMock()
    mock_settings.elevenlabs_api_key.get_secret_value.return_value = "k"
    monkeypatch.setattr(ws_module, "get_settings", lambda: mock_settings)

    async def empty_chunks() -> AsyncIterator[str]:
        if False:
            yield ""

    collected = [b async for b in ws_stream(empty_chunks(), voice_id="v")]
    assert collected == []
    payloads = [json.loads(s) for s in fake.sent]
    assert payloads[0] == {"text": " "} and payloads[-1] == {"text": ""}
    assert len(payloads) == 2
