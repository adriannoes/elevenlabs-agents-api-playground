"""Integration: vendor TTS benchmark (optional VCR)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from eleven_demo.benchmarks.tts_vendor import run_vendor_benchmark
from eleven_demo.config import get_settings

if TYPE_CHECKING:
    from pytest import FixtureRequest

# Must match the ElevenLabs TTS stream path and OpenAI credential checks during VCR replay.
_VENDOR_CASSETTE_DEFAULT_PT_VOICE_ID = "hpp4J3VqNfWAUOO0d1Us"
_OPENAI_PLACEHOLDER_KEY_FOR_VCR_REPLAY = "sk-vcr-openai-replay-placeholder"


def _both_keys_set() -> bool:
    return bool(
        os.environ.get("ELEVENLABS_API_KEY", "").strip()
        and os.environ.get("OPENAI_API_KEY", "").strip()
    )


@pytest.mark.integration
@pytest.mark.vcr(
    filter_headers=["xi-api-key", "authorization"],
    record_mode="once",
)
def test_vendor_benchmark_one_round_vcr(
    request: FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cassette = Path(request.node.path).parent / "cassettes" / f"{request.node.name}.yaml"
    if not cassette.is_file() and not _both_keys_set():
        pytest.skip(
            "Needs ELEVENLABS_API_KEY and OPENAI_API_KEY to record once, "
            f"or commit sanitized cassette at {cassette}",
        )

    replay = cassette.is_file()
    if replay:
        if not os.environ.get("DEFAULT_PT_VOICE_ID", "").strip():
            monkeypatch.setenv("DEFAULT_PT_VOICE_ID", _VENDOR_CASSETTE_DEFAULT_PT_VOICE_ID)
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            monkeypatch.setenv("OPENAI_API_KEY", _OPENAI_PLACEHOLDER_KEY_FOR_VCR_REPLAY)

    elif not os.environ.get("DEFAULT_PT_VOICE_ID", "").strip():
        pytest.skip(
            "DEFAULT_PT_VOICE_ID is required to record the ElevenLabs benchmark leg "
            f"(URLs must stay stable vs the committed cassette at {cassette}).",
        )

    get_settings.cache_clear()
    run_vendor_benchmark(["Integration vendor benchmark smoke."], 1, randomize_order=False)
    get_settings.cache_clear()
