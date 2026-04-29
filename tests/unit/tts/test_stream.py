"""Unit tests for HTTP streaming TTS."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

import eleven_demo.tts.stream as stream_module
from eleven_demo.tts.stream import stream

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_stream_sets_ttfb_only_on_first_chunk(monkeypatch: MonkeyPatch) -> None:
    clock = iter([1000.0, 1000.025])

    monkeypatch.setattr(stream_module, "perf_counter", lambda: next(clock))

    mock_client = MagicMock()
    mock_client.text_to_speech.stream.return_value = iter([b"a", b"b", b"c"])
    monkeypatch.setattr(stream_module, "get_client", lambda: mock_client)

    chunks = list(stream("hello", voice_id="voice-1"))

    assert chunks[0][0] == b"a"
    assert chunks[0][1] == pytest.approx(0.025)
    assert chunks[1:] == [(b"b", None), (b"c", None)]

    kw = mock_client.text_to_speech.stream.call_args.kwargs
    assert kw == {
        "voice_id": "voice-1",
        "text": "hello",
        "model_id": "eleven_flash_v2_5",
        "output_format": "mp3_22050_32",
    }


def test_stream_empty_iteration(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(stream_module, "perf_counter", lambda: 0.0)

    mock_client = MagicMock()
    mock_client.text_to_speech.stream.return_value = iter([])
    monkeypatch.setattr(stream_module, "get_client", lambda: mock_client)

    assert list(stream("x", voice_id="voice-1")) == []
