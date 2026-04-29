"""Realtime Speech-to-Text over WebSocket (streaming audio in)."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from collections.abc import AsyncIterable, AsyncIterator
from typing import Any
from urllib.parse import urlencode

import websockets

from eleven_demo.config import get_settings
from eleven_demo.stt.types import TranscriptEvent

logger = logging.getLogger(__name__)

REALTIME_WS_HOST = "wss://api.elevenlabs.io"
REALTIME_DEFAULT_SAMPLE_RATE = 16000

_REALTIME_ERROR_MESSAGE_TYPES = frozenset(
    {
        "error",
        "auth_error",
        "quota_exceeded",
        "commit_throttled",
        "unaccepted_terms",
        "rate_limited",
        "queue_overflow",
        "resource_exhausted",
        "session_time_limit_exceeded",
        "input_error",
        "chunk_size_exceeded",
        "insufficient_audio_activity",
        "transcriber_error",
    }
)


def _realtime_uri(*, model_id: str, language_code: str) -> str:
    params = {
        "model_id": model_id,
        "audio_format": "pcm_16000",
        "commit_strategy": "manual",
        "language_code": language_code,
    }
    return f"{REALTIME_WS_HOST}/v1/speech-to-text/realtime?{urlencode(params)}"


def _map_server_payload(payload: dict[str, Any]) -> TranscriptEvent | None:
    mt = payload.get("message_type")
    if mt == "partial_transcript":
        text = str(payload.get("text", ""))
        return TranscriptEvent(type=mt, text=text, is_partial=True)
    if mt in ("committed_transcript", "committed_transcript_with_timestamps"):
        text = str(payload.get("text", ""))
        return TranscriptEvent(type=str(mt), text=text, is_partial=False)
    return None


def _raise_if_error_payload(payload: dict[str, Any]) -> None:
    mt = payload.get("message_type")
    if mt in _REALTIME_ERROR_MESSAGE_TYPES:
        msg = str(payload.get("error", "speech-to-text error"))
        raise RuntimeError(f"{mt}: {msg}")


async def realtime_transcribe(
    audio_chunks: AsyncIterable[bytes],
    *,
    model_id: str | None = None,
    language_code: str = "por",
) -> AsyncIterator[TranscriptEvent]:
    """Stream PCM audio chunks to realtime STT and yield transcript events.

    Audio chunks must be **mono PCM signed 16-bit little-endian** at
    :data:`REALTIME_DEFAULT_SAMPLE_RATE` Hz, matching ``audio_format=pcm_16000`` on the wire.
    """
    settings = get_settings()
    resolved_model = model_id or settings.stt_realtime_model_id
    uri = _realtime_uri(model_id=resolved_model, language_code=language_code)
    headers = {"xi-api-key": settings.elevenlabs_api_key.get_secret_value()}
    sample_rate = REALTIME_DEFAULT_SAMPLE_RATE

    queue: asyncio.Queue[TranscriptEvent | None] = asyncio.Queue()

    async with websockets.connect(uri, additional_headers=headers) as ws:

        async def receiver_side() -> None:
            try:
                async for raw in ws:
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        logger.warning("Realtime STT invalid JSON: %s", exc)
                        continue
                    if not isinstance(payload, dict):
                        continue
                    _raise_if_error_payload(payload)
                    mapped = _map_server_payload(payload)
                    if mapped is not None:
                        await queue.put(mapped)
            finally:
                await queue.put(None)

        async def sender_side() -> None:
            try:
                async for chunk in audio_chunks:
                    msg = {
                        "message_type": "input_audio_chunk",
                        "audio_base_64": base64.b64encode(chunk).decode("ascii"),
                        "commit": False,
                        "sample_rate": sample_rate,
                    }
                    await ws.send(json.dumps(msg))
                commit_msg = {
                    "message_type": "input_audio_chunk",
                    "audio_base_64": "",
                    "commit": True,
                    "sample_rate": sample_rate,
                }
                await ws.send(json.dumps(commit_msg))
            finally:
                await ws.close()

        recv_task = asyncio.create_task(receiver_side())
        send_task = asyncio.create_task(sender_side())
        try:
            while True:
                ev = await queue.get()
                if ev is None:
                    break
                yield ev
        finally:
            results = await asyncio.gather(recv_task, send_task, return_exceptions=True)
            for item in results:
                if isinstance(item, BaseException):
                    raise item
