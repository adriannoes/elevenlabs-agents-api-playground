"""Integration: batch STT (VCR)."""

from __future__ import annotations

from pathlib import Path

import pytest

from eleven_demo.stt.batch import transcribe

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SAMPLE = _REPO_ROOT / "data" / "samples" / "hello-pt-br.mp3"


@pytest.mark.integration
@pytest.mark.vcr(
    filter_headers=["xi-api-key", "authorization"],
    record_mode="once",
)
def test_batch_transcribe_pt_br_sample() -> None:
    assert _SAMPLE.is_file(), f"Missing sample audio: {_SAMPLE}"

    result = transcribe(_SAMPLE)

    assert result.text
    lowered = result.text.lower()
    assert "demonstração" in lowered or "demonstracao" in lowered
