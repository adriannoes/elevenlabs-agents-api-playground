"""HTTP streaming text-to-speech with optional TTFB tagging on the first chunk."""

from __future__ import annotations

from collections.abc import Iterator
from time import perf_counter

from eleven_demo.client import get_client


def stream(
    text: str,
    *,
    voice_id: str,
    model_id: str = "eleven_flash_v2_5",
    output_format: str = "mp3_22050_32",
) -> Iterator[tuple[bytes, float | None]]:
    """Yield audio chunks; the first tuple includes time-to-first-byte in seconds."""
    client = get_client()
    t0 = perf_counter()
    ttfb_seconds: float | None = None

    audio_iter = client.text_to_speech.stream(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        output_format=output_format,
    )

    for chunk in audio_iter:
        if ttfb_seconds is None:
            ttfb_seconds = perf_counter() - t0
            yield chunk, ttfb_seconds
        else:
            yield chunk, None
