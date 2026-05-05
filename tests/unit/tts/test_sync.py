"""Unit tests for synchronous TTS."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from eleven_demo.tts.sync import synthesize

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def _make_convert_context(mock_http: MagicMock) -> MagicMock:
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_http)
    cm.__exit__ = MagicMock(return_value=None)
    return cm


def test_synthesize_concatenates_chunks_and_returns_metadata(monkeypatch: MonkeyPatch) -> None:
    mock_http = MagicMock()
    mock_http.headers = {"x-character-count": "42", "request-id": "req-xyz"}
    mock_http.data = iter([b"\xff", b"\xfb", b"\x90"])

    mock_client = MagicMock()
    mock_client.text_to_speech.with_raw_response.convert.return_value = _make_convert_context(
        mock_http
    )

    monkeypatch.setattr("eleven_demo.tts.sync.get_client", lambda: mock_client)

    audio, meta = synthesize("hello", voice_id="voice-1", model_id="eleven_flash_v2_5")

    assert audio == b"\xff\xfb\x90"
    assert meta["character_count"] == 42
    assert meta["request_id"] == "req-xyz"
    assert meta["model_id"] == "eleven_flash_v2_5"
    assert meta["output_format"] == "mp3_22050_32"
    assert meta["apply_text_normalization"] == "auto"

    kwargs = mock_client.text_to_speech.with_raw_response.convert.call_args.kwargs
    assert kwargs["voice_id"] == "voice-1"
    assert kwargs["text"] == "hello"
    assert kwargs["model_id"] == "eleven_flash_v2_5"
    assert kwargs["output_format"] == "mp3_22050_32"
    assert "voice_settings" not in kwargs
    assert "apply_text_normalization" not in kwargs


def test_synthesize_passes_apply_text_normalization_when_on(monkeypatch: MonkeyPatch) -> None:
    mock_http = MagicMock()
    mock_http.headers = {"x-character-count": "1", "request-id": ""}
    mock_http.data = iter([b"z"])

    mock_client = MagicMock()
    mock_client.text_to_speech.with_raw_response.convert.return_value = _make_convert_context(
        mock_http
    )

    monkeypatch.setattr("eleven_demo.tts.sync.get_client", lambda: mock_client)

    synthesize("z", voice_id="v", apply_text_normalization="on")

    kwargs = mock_client.text_to_speech.with_raw_response.convert.call_args.kwargs
    assert kwargs["apply_text_normalization"] == "on"


def test_synthesize_voice_settings_validated_when_passed(monkeypatch: MonkeyPatch) -> None:
    mock_http = MagicMock()
    mock_http.headers = {"x-character-count": "10", "request-id": "r"}
    mock_http.data = iter([b"a"])

    mock_client = MagicMock()
    mock_client.text_to_speech.with_raw_response.convert.return_value = _make_convert_context(
        mock_http
    )

    monkeypatch.setattr("eleven_demo.tts.sync.get_client", lambda: mock_client)

    vs = {
        "stability": 0.4,
        "similarity_boost": 0.85,
        "style": 0.4,
        "use_speaker_boost": True,
    }
    synthesize("x", voice_id="vid", voice_settings=vs)

    kwargs = mock_client.text_to_speech.with_raw_response.convert.call_args.kwargs
    inner_vs = kwargs["voice_settings"]
    assert inner_vs.stability == 0.4
    assert inner_vs.use_speaker_boost is True


def test_character_cost_header_preferred_over_legacy_count(monkeypatch: MonkeyPatch) -> None:
    mock_http = MagicMock()
    mock_http.headers = {"character-cost": "99", "x-character-count": "42", "request-id": "r"}
    mock_http.data = iter([b"x"])

    mock_client = MagicMock()
    mock_client.text_to_speech.with_raw_response.convert.return_value = _make_convert_context(
        mock_http
    )

    monkeypatch.setattr("eleven_demo.tts.sync.get_client", lambda: mock_client)

    _audio, meta = synthesize("hello", voice_id="voice-1")
    assert meta["character_count"] == 99


def test_character_count_defaults_on_bad_header(monkeypatch: MonkeyPatch) -> None:
    mock_http = MagicMock()
    mock_http.headers = {"character-cost": "not-int", "request-id": ""}
    mock_http.data = iter([b""])

    mock_client = MagicMock()
    mock_client.text_to_speech.with_raw_response.convert.return_value = _make_convert_context(
        mock_http
    )

    monkeypatch.setattr("eleven_demo.tts.sync.get_client", lambda: mock_client)

    _audio, meta = synthesize(".", voice_id="voice-1")
    assert meta["character_count"] == 0


def test_raises_validation_error_when_voice_settings_invalid(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("eleven_demo.tts.sync.get_client", MagicMock())

    with pytest.raises(ValidationError):
        synthesize("hi", voice_id="vid", voice_settings={"stability": "bad"})
