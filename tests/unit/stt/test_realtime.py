"""Unit tests for realtime STT WebSocket streaming."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest

from eleven_demo.stt import realtime as realtime_module
from eleven_demo.stt.realtime import realtime_transcribe


class _FakeWs:
    """Minimal async WebSocket with ordered inbound frames."""

    def __init__(self, incoming: list[str]) -> None:
        self._incoming = incoming
        self._idx = 0
        self.sent: list[str] = []

    async def send(self, data: str) -> None:
        self.sent.append(data)

    async def close(self) -> None:
        return None

    def __aiter__(self) -> _FakeWs:
        return self

    async def __anext__(self) -> str:
        await asyncio.sleep(0)
        if self._idx >= len(self._incoming):
            raise StopAsyncIteration
        msg = self._incoming[self._idx]
        self._idx += 1
        return msg


class _AsyncConnectCm:
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
async def test_realtime_transcribe_maps_partial_and_committed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incoming = [
        json.dumps({"message_type": "session_started", "session_id": "s1", "config": {}}),
        json.dumps({"message_type": "partial_transcript", "text": "Ol"}),
        json.dumps({"message_type": "committed_transcript", "text": "Olá."}),
    ]
    fake = _FakeWs(incoming)
    captured: dict[str, str] = {}

    def fake_connect(uri: str, **kwargs: object) -> _AsyncConnectCm:
        captured["uri"] = uri
        assert kwargs["additional_headers"]["xi-api-key"] == "key"
        return _AsyncConnectCm(fake)

    monkeypatch.setattr(realtime_module.websockets, "connect", fake_connect)

    mock_settings = MagicMock()
    mock_settings.stt_realtime_model_id = "scribe_v2_realtime"
    mock_settings.elevenlabs_api_key.get_secret_value.return_value = "key"
    monkeypatch.setattr(realtime_module, "get_settings", lambda: mock_settings)

    pcm = b"\x00\x01" * 64

    async def chunks() -> AsyncIterator[bytes]:
        yield pcm

    events = [e async for e in realtime_transcribe(chunks(), language_code="por")]

    assert len(events) == 2
    assert events[0].type == "partial_transcript"
    assert events[0].text == "Ol"
    assert events[0].is_partial is True
    assert events[1].type == "committed_transcript"
    assert events[1].text == "Olá."
    assert events[1].is_partial is False

    assert "model_id=scribe_v2_realtime" in captured["uri"]
    assert "language_code=por" in captured["uri"]

    payloads = [json.loads(s) for s in fake.sent]
    assert payloads[0]["message_type"] == "input_audio_chunk"
    assert payloads[0]["commit"] is False
    assert payloads[0]["sample_rate"] == 16000
    assert payloads[-1]["commit"] is True
    assert payloads[-1]["audio_base_64"] == ""


@pytest.mark.asyncio
async def test_realtime_transcribe_respects_explicit_model_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeWs(
        [
            json.dumps({"message_type": "committed_transcript", "text": "done"}),
        ],
    )

    captured: dict[str, str] = {}

    def fake_connect(uri: str, **_: object) -> _AsyncConnectCm:
        captured["uri"] = uri
        return _AsyncConnectCm(fake)

    monkeypatch.setattr(realtime_module.websockets, "connect", fake_connect)

    mock_settings = MagicMock()
    mock_settings.stt_realtime_model_id = "scribe_v2_realtime"
    mock_settings.elevenlabs_api_key.get_secret_value.return_value = "k"
    monkeypatch.setattr(realtime_module, "get_settings", lambda: mock_settings)

    async def one_chunk() -> AsyncIterator[bytes]:
        yield b"\x00\x00"

    async for _ in realtime_transcribe(one_chunk(), model_id="custom_model"):
        pass

    assert "model_id=custom_model" in captured["uri"]


@pytest.mark.asyncio
async def test_realtime_transcribe_raises_on_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeWs(
        [
            json.dumps({"message_type": "error", "error": "bad input"}),
        ],
    )

    monkeypatch.setattr(
        realtime_module.websockets,
        "connect",
        lambda *_a, **_k: _AsyncConnectCm(fake),
    )

    mock_settings = MagicMock()
    mock_settings.stt_realtime_model_id = "scribe_v2_realtime"
    mock_settings.elevenlabs_api_key.get_secret_value.return_value = "k"
    monkeypatch.setattr(realtime_module, "get_settings", lambda: mock_settings)

    async def one_chunk() -> AsyncIterator[bytes]:
        yield b"\x00\x00"

    with pytest.raises(RuntimeError, match="bad input"):
        async for _ in realtime_transcribe(one_chunk()):
            pass
