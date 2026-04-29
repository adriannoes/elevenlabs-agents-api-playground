"""Integration: synchronous TTS (VCR)."""

from __future__ import annotations

import pytest

from eleven_demo.tts.sync import synthesize

_DEMO_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
_SHORT_TEXT = "Integration sync smoke test."


def _assert_mp3_magic(audio: bytes) -> None:
    assert audio.startswith((b"ID3", b"\xff\xfb")), audio[:16]


@pytest.mark.integration
@pytest.mark.vcr(
    filter_headers=["xi-api-key", "authorization"],
    record_mode="once",
)
def test_synthesize_returns_mp3_and_character_cost() -> None:
    audio, metadata = synthesize(
        _SHORT_TEXT,
        voice_id=_DEMO_VOICE_ID,
        model_id="eleven_flash_v2_5",
        output_format="mp3_22050_32",
    )

    _assert_mp3_magic(audio)
    assert metadata["character_count"] > 0
    assert metadata["model_id"] == "eleven_flash_v2_5"
