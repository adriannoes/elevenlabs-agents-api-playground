"""Integration: HTTP streaming TTS (VCR).

Streaming responses omit billing headers in ``tts.stream.stream``; character billing for the same
text shape is validated synchronously in ``test_integration_sync``.
"""

from __future__ import annotations

import pytest

from eleven_demo.tts.stream import stream

_DEMO_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
_SHORT_TEXT = "Integration stream smoke test."


def _assert_mp3_magic(audio: bytes) -> None:
    assert audio.startswith((b"ID3", b"\xff\xfb")), audio[:16]


@pytest.mark.integration
@pytest.mark.vcr(
    filter_headers=["xi-api-key", "authorization"],
    record_mode="once",
)
def test_stream_yields_mp3_chunks_and_ttfb() -> None:
    chunks: list[bytes] = []
    first_ttfb: float | None = None
    for chunk, ttfb in stream(
        _SHORT_TEXT,
        voice_id=_DEMO_VOICE_ID,
        model_id="eleven_flash_v2_5",
        output_format="mp3_22050_32",
    ):
        chunks.append(chunk)
        if first_ttfb is None:
            first_ttfb = ttfb

    combined = b"".join(chunks)
    assert combined
    _assert_mp3_magic(combined)
    assert first_ttfb is not None
    assert first_ttfb >= 0.0
