"""Unit tests for the PT-BR voice listing CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts import voices_pt_br

from eleven_demo.voices.catalog import VoiceCard

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def test_cli_prints_fallback_guidance_when_no_pt_br_voices(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr(voices_pt_br, "list_pt_br_voices", lambda page_size: [])
    monkeypatch.setattr(
        voices_pt_br,
        "list_voices",
        lambda page_size: [
            VoiceCard(voice_id="v1", name="Fallback Voice", language="en"),
        ],
    )
    monkeypatch.setattr("sys.argv", ["voices_pt_br.py"])

    voices_pt_br.main()

    printed = capsys.readouterr().out
    assert "No PT-BR-labelled voices found" in printed
    assert "Fallback Voice" in printed
    assert "DEFAULT_PT_VOICE_ID" in printed
