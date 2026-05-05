"""Unit tests for benchmarks/openai_tts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from eleven_demo.benchmarks.openai_tts import parse_openai_response_format, stream_openai_tts
from eleven_demo.config import get_settings

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_parse_openai_response_format_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        parse_openai_response_format("gif")


def test_stream_openai_tts_raises_without_api_key(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        next(
            stream_openai_tts(
                "hi",
                model_id="gpt-4o-mini-tts",
                voice="coral",
                response_format="mp3",
            )
        )

    get_settings.cache_clear()


def test_stream_openai_tts_yields_ttfb_on_first_chunk(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    get_settings.cache_clear()

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.iter_bytes.return_value = iter([b"a", b"b"])

    mock_client = MagicMock()
    mock_client.audio.speech.with_streaming_response.create.return_value = mock_response

    clock = iter([1.0, 1.02, 1.02])
    monkeypatch.setattr(
        "eleven_demo.benchmarks.openai_tts.perf_counter",
        lambda: next(clock),
    )
    monkeypatch.setattr(
        "eleven_demo.benchmarks.openai_tts.OpenAI",
        lambda **kwargs: mock_client,
    )

    chunks = list(
        stream_openai_tts(
            "hello",
            model_id="gpt-4o-mini-tts",
            voice="coral",
            response_format="mp3",
        )
    )

    assert chunks[0][0] == b"a"
    assert chunks[0][1] == pytest.approx(0.02)
    assert chunks[1] == (b"b", None)
    get_settings.cache_clear()
