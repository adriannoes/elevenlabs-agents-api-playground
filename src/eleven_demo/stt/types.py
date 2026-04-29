"""Speech-to-text types (ElevenLabs SDK re-exports + realtime events)."""

from __future__ import annotations

from elevenlabs import SpeechToTextChunkResponseModel, SpeechToTextConvertResponse
from pydantic import BaseModel, ConfigDict, Field

Transcript = SpeechToTextConvertResponse


class TranscriptEvent(BaseModel):
    """Realtime STT item mapped from WebSocket ``message_type`` payloads."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: str = Field(description="Server ``message_type`` (e.g. partial_transcript).")
    text: str
    is_partial: bool


__all__ = [
    "SpeechToTextChunkResponseModel",
    "SpeechToTextConvertResponse",
    "Transcript",
    "TranscriptEvent",
]
