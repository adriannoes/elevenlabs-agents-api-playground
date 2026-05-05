"""Synchronous HTTP text-to-speech."""

from __future__ import annotations

from typing import Any, Literal

from elevenlabs.types.voice_settings import VoiceSettings

from eleven_demo.client import get_client

ApplyTextNormalization = Literal["auto", "on", "off"]


def synthesize(
    text: str,
    *,
    voice_id: str,
    model_id: str = "eleven_flash_v2_5",
    output_format: str = "mp3_22050_32",
    voice_settings: dict[str, Any] | None = None,
    apply_text_normalization: ApplyTextNormalization = "auto",
) -> tuple[bytes, dict[str, Any]]:
    """Convert text to speech and return concatenated audio plus billing/trace metadata."""
    client = get_client()

    kwargs: dict[str, Any] = {
        "voice_id": voice_id,
        "text": text,
        "model_id": model_id,
        "output_format": output_format,
    }
    if voice_settings is not None:
        kwargs["voice_settings"] = VoiceSettings.model_validate(voice_settings)
    if apply_text_normalization != "auto":
        kwargs["apply_text_normalization"] = apply_text_normalization

    with client.text_to_speech.with_raw_response.convert(**kwargs) as http_response:
        headers = dict(http_response.headers)
        try:
            audio = b"".join(http_response.data)
        finally:
            http_response.close()

    char_hdr = headers.get("character-cost") or headers.get("x-character-count", "0")
    try:
        character_count = int(char_hdr)
    except ValueError:
        character_count = 0

    metadata: dict[str, Any] = {
        "character_count": character_count,
        "request_id": headers.get("request-id", ""),
        "model_id": model_id,
        "output_format": output_format,
        "apply_text_normalization": apply_text_normalization,
    }
    return audio, metadata
