"""Unit tests for the local FastAPI WebSocket bridge."""

from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator
from types import SimpleNamespace
from typing import TYPE_CHECKING

from apps.ws_bridge import main as bridge
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_convai_demo_tools_returns_mock_lookup() -> None:
    client = TestClient(bridge.app)
    response = client.post("/convai/demo-tools", json={"cpf": "12345678900"})

    assert response.status_code == 200
    data = response.json()
    assert data["account_ref_masked"] == "***8900"


def test_convai_demo_tools_rejects_non_object_json() -> None:
    client = TestClient(bridge.app)
    response = client.post("/convai/demo-tools", json=[])

    assert response.status_code == 400


def test_convai_demo_tools_rejects_unknown_body() -> None:
    client = TestClient(bridge.app)
    response = client.post("/convai/demo-tools", json={"not_a_parameter": True})

    assert response.status_code == 422


def test_healthz_returns_ok() -> None:
    client = TestClient(bridge.app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ws_tts_streams_binary_audio(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def fake_ws_stream(
        text_chunks: AsyncIterable[str],
        *,
        voice_id: str,
        model_id: str,
        output_format: str,
    ) -> AsyncIterator[bytes]:
        captured["text_chunks"] = [chunk async for chunk in text_chunks]
        captured["voice_id"] = voice_id
        captured["model_id"] = model_id
        captured["output_format"] = output_format
        yield b"audio-1"
        yield b"audio-2"

    monkeypatch.setattr(bridge, "ws_stream", fake_ws_stream)
    monkeypatch.setattr(
        bridge,
        "get_settings",
        lambda: SimpleNamespace(
            default_pt_voice_id="voice-pt",
            tts_model_id="eleven_flash_v2_5",
            tts_output_format="mp3_22050_32",
        ),
    )

    client = TestClient(bridge.app)
    with client.websocket_connect("/ws/tts") as websocket:
        websocket.send_json({"text": "Olá mundo"})

        assert websocket.receive_bytes() == b"audio-1"
        assert websocket.receive_bytes() == b"audio-2"

    assert captured == {
        "text_chunks": ["Olá mundo"],
        "voice_id": "voice-pt",
        "model_id": "eleven_flash_v2_5",
        "output_format": "mp3_22050_32",
    }


def test_ws_tts_rejects_invalid_payload(monkeypatch: MonkeyPatch) -> None:
    async def fake_ws_stream(
        text_chunks: AsyncIterable[str],
        *,
        voice_id: str,
        model_id: str,
        output_format: str,
    ) -> AsyncIterator[bytes]:
        msg = "ws_stream should not run for invalid input"
        raise AssertionError(msg)
        yield b""  # pragma: no cover

    monkeypatch.setattr(bridge, "ws_stream", fake_ws_stream)

    client = TestClient(bridge.app)
    with client.websocket_connect("/ws/tts") as websocket:
        websocket.send_json({"text": "hello", "extra": True})

        assert websocket.receive_json() == {
            "error": "Invalid payload. Send JSON with only a non-empty text field.",
        }
