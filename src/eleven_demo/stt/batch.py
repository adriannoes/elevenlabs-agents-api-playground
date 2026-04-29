"""Batch (non-streaming) speech-to-text transcription."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from eleven_demo.client import get_client
from eleven_demo.stt.types import Transcript


def transcribe(
    file_path: Path,
    *,
    language: str = "por",
    model_id: str = "scribe_v1",
    diarize: bool = True,
    tag_audio_events: bool = True,
) -> Transcript:
    """Transcribe an audio file using batch STT and return the SDK response model."""
    client = get_client()
    with file_path.open("rb") as audio_file:
        return cast(
            Transcript,
            client.speech_to_text.convert(
                file=audio_file,
                model_id=model_id,
                language_code=language,
                diarize=diarize,
                tag_audio_events=tag_audio_events,
            ),
        )
