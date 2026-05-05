"""Unit tests for the Voice Isolator CLI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from elevenlabs.core import ApiError
from scripts import voice_isolator_demo

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest import TempPathFactory


def test_voice_isolator_writes_chunks_and_prints_summary(
    monkeypatch: MonkeyPatch,
    tmp_path_factory: TempPathFactory,
    capsys: CaptureFixture[str],
) -> None:
    tmp_path = tmp_path_factory.mktemp("voice-isolator")
    inp = tmp_path / "noisy.mp3"
    out = tmp_path / "clean.mp3"
    inp.write_bytes(b"noisy-audio")

    captured: dict[str, object] = {}

    def fake_convert(**kwargs: object) -> list[bytes]:
        audio = kwargs["audio"]
        assert hasattr(audio, "read")
        captured["input_bytes"] = audio.read()
        captured["file_format"] = kwargs["file_format"]
        return [b"clean-", b"audio"]

    client = MagicMock()
    client.audio_isolation.convert.side_effect = fake_convert
    monkeypatch.setattr(voice_isolator_demo, "get_client", lambda: client)
    monkeypatch.setattr(
        voice_isolator_demo.time,
        "perf_counter",
        MagicMock(side_effect=[10.0, 12.5]),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "voice_isolator_demo.py",
            str(inp),
            "--out",
            str(out),
            "--file-format",
            "pcm_s16le_16",
        ],
    )

    voice_isolator_demo.main()

    assert out.read_bytes() == b"clean-audio"
    assert captured == {"input_bytes": b"noisy-audio", "file_format": "pcm_s16le_16"}
    printed = capsys.readouterr().out
    assert "Voice Isolator" in printed
    assert "input_bytes" in printed
    assert "elapsed_seconds  2.50" in printed
    assert "scripts/stt_demo.py" in printed


def test_voice_isolator_rejects_missing_input(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.mp3"
    monkeypatch.setattr(sys, "argv", ["voice_isolator_demo.py", str(missing)])

    with pytest.raises(SystemExit, match="Audio not found"):
        voice_isolator_demo.main()


def test_voice_isolator_reports_api_errors_without_traceback(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    inp = tmp_path / "short.mp3"
    out = tmp_path / "clean.mp3"
    inp.write_bytes(b"short")

    client = MagicMock()
    client.audio_isolation.convert.side_effect = ApiError(
        status_code=400,
        body={"detail": {"message": "Audio duration is below the minimum."}},
    )
    monkeypatch.setattr(voice_isolator_demo, "get_client", lambda: client)
    monkeypatch.setattr(
        sys,
        "argv",
        ["voice_isolator_demo.py", str(inp), "--out", str(out)],
    )

    with pytest.raises(SystemExit, match="Voice Isolator failed: 400"):
        voice_isolator_demo.main()

    assert not out.exists()
