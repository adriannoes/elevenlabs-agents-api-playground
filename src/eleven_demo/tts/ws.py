"""WebSocket text-to-speech (input streaming)."""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import AsyncIterable, AsyncIterator
from urllib.parse import urlencode

import websockets

from eleven_demo.config import get_settings


def _stream_input_uri(voice_id: str, *, model_id: str, output_format: str) -> str:
    query = urlencode({"model_id": model_id, "output_format": output_format})
    return f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?{query}"


async def ws_stream(
    text_chunks: AsyncIterable[str],
    *,
    voice_id: str,
    model_id: str = "eleven_flash_v2_5",
    output_format: str = "mp3_22050_32",
) -> AsyncIterator[bytes]:
    """Stream TTS audio over ElevenLabs WebSocket input-streaming."""
    uri = _stream_input_uri(voice_id, model_id=model_id, output_format=output_format)
    headers = {"xi-api-key": get_settings().elevenlabs_api_key.get_secret_value()}

    async with websockets.connect(uri, additional_headers=headers) as ws:
        await ws.send(json.dumps({"text": " "}))
        async for chunk in text_chunks:
            payload = {"text": f"{chunk} ", "try_trigger_generation": True}
            await ws.send(json.dumps(payload))
        await ws.send(json.dumps({"text": ""}))
        async for raw in ws:
            msg = json.loads(raw)
            b64_audio = msg.get("audio")
            if isinstance(b64_audio, str) and b64_audio:
                try:
                    decoded = base64.b64decode(b64_audio)
                except (binascii.Error, ValueError):
                    decoded = b""
                if decoded:
                    yield decoded
            if msg.get("isFinal"):
                break
