"""OpenAI Text-to-speech streaming for vendor benchmark comparisons."""

from __future__ import annotations

from collections.abc import Iterator
from time import perf_counter
from typing import Literal, cast

from openai import OpenAI

from eleven_demo.config import get_settings

OpenAiSpeechFormat = Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]
_ALLOWED_FORMATS: frozenset[str] = frozenset({"mp3", "opus", "aac", "flac", "wav", "pcm"})


def parse_openai_response_format(value: str) -> OpenAiSpeechFormat:
    """Validate OpenAI speech ``response_format`` from settings or CLI."""
    if value not in _ALLOWED_FORMATS:
        msg = f"Unsupported OpenAI TTS response_format: {value!r}"
        raise ValueError(msg)
    return cast(OpenAiSpeechFormat, value)


def stream_openai_tts(
    text: str,
    *,
    model_id: str,
    voice: str,
    response_format: OpenAiSpeechFormat,
) -> Iterator[tuple[bytes, float | None]]:
    """Stream speech audio chunks; first tuple includes TTFB in seconds."""
    settings = get_settings()
    key = settings.openai_api_key
    if key is None or not key.get_secret_value().strip():
        msg = "OPENAI_API_KEY is not set; vendor benchmark requires a valid OpenAI API key."
        raise RuntimeError(msg)

    client = OpenAI(api_key=key.get_secret_value())
    t0 = perf_counter()
    ttfb: float | None = None

    with client.audio.speech.with_streaming_response.create(
        model=model_id,
        voice=voice,
        input=text,
        response_format=response_format,
    ) as response:
        for chunk in response.iter_bytes():
            if ttfb is None:
                ttfb = perf_counter() - t0
                yield chunk, ttfb
            else:
                yield chunk, None
