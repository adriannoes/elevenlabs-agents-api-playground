"""Local-only FastAPI bridge from browser WebSocket clients to ElevenLabs TTS."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from eleven_demo.agents.tool_webhook import dispatch_convai_demo_tool
from eleven_demo.config import get_settings
from eleven_demo.tts.ws import ws_stream

logger = logging.getLogger(__name__)

MAX_TTS_TEXT_CHARS = 1_000
INVALID_PAYLOAD_MESSAGE = "Invalid payload. Send JSON with only a non-empty text field."
MISSING_VOICE_MESSAGE = "DEFAULT_PT_VOICE_ID is required before using /ws/tts."
BRIDGE_FAILURE_MESSAGE = "TTS bridge failed while streaming audio."
INVALID_JSON_TOOLS_MESSAGE = "Body must be valid JSON."
TOOLS_JSON_OBJECT_MESSAGE = "JSON body must be an object."

app = FastAPI(
    title="ElevenLabs Local Dev Bridge",
    description=(
        "Local helpers: deterministic Convai tool webhooks and TTS streaming. "
        "Do not expose without TLS, authentication, and rate limiting."
    ),
)


class TtsRequest(BaseModel):
    """Client payload accepted by `/ws/tts`."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(min_length=1, max_length=MAX_TTS_TEXT_CHARS)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Return a lightweight liveness response."""
    return {"status": "ok"}


@app.post("/convai/demo-tools")
async def convai_demo_tools(request: Request) -> JSONResponse:
    """Serve deterministic mocks for Conversational AI server webhook tools."""
    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=INVALID_JSON_TOOLS_MESSAGE
        ) from None

    if not isinstance(body, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=TOOLS_JSON_OBJECT_MESSAGE,
        )

    try:
        result = dispatch_convai_demo_tool(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return JSONResponse(content=result)


@app.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket) -> None:
    """Accept text messages and return ElevenLabs TTS audio as binary frames."""
    await websocket.accept()

    while True:
        try:
            payload = await websocket.receive_json()
        except WebSocketDisconnect:
            return
        except ValueError:
            await websocket.send_json({"error": INVALID_PAYLOAD_MESSAGE})
            continue

        try:
            request = TtsRequest.model_validate(payload)
        except ValidationError:
            await websocket.send_json({"error": INVALID_PAYLOAD_MESSAGE})
            continue

        settings = get_settings()
        if not settings.default_pt_voice_id:
            await websocket.send_json({"error": MISSING_VOICE_MESSAGE})
            continue

        try:
            async for chunk in ws_stream(
                _single_text_chunk(request.text),
                voice_id=settings.default_pt_voice_id,
                model_id=settings.tts_model_id,
                output_format=settings.tts_output_format,
            ):
                await websocket.send_bytes(chunk)
        except WebSocketDisconnect:
            return
        except Exception:
            logger.exception("TTS bridge stream failed")
            await websocket.send_json({"error": BRIDGE_FAILURE_MESSAGE})
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return


async def _single_text_chunk(text: str) -> AsyncIterator[str]:
    """Yield one validated text chunk for `ws_stream`."""
    yield text
