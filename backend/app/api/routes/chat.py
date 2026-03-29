"""Chat session/message endpoints."""

import json
import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse

from app.models.schemas import (
    ChatExportFormat,
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ChatMessagesResponse,
    ChatSessionCreateRequest,
    ChatSessionResponse,
)
from app.services.chat_service import ChatServiceError, get_chat_service

router = APIRouter()
logger = logging.getLogger(__name__)


def _typed_error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_chat_session(request: ChatSessionCreateRequest):
    """Create a persistent chat session for repo/podcast context."""
    service = get_chat_service()
    try:
        return await service.create_session(request)
    except ChatServiceError as exc:
        raise _typed_error(exc.code, exc.message, exc.status_code)
    except Exception:
        logger.exception("Failed to create chat session")
        raise _typed_error("CHAT_SESSION_CREATE_FAILED", "Failed to create chat session.", 500)


@router.get("/{session_id}/messages", response_model=ChatMessagesResponse)
async def get_chat_messages(session_id: str):
    """Return all persisted messages for a chat session."""
    service = get_chat_service()
    try:
        return await service.get_messages(session_id=session_id)
    except ChatServiceError as exc:
        raise _typed_error(exc.code, exc.message, exc.status_code)
    except Exception:
        logger.exception("Failed to load chat messages", extra={"session_id": session_id})
        raise _typed_error("CHAT_MESSAGES_LOAD_FAILED", "Failed to load chat messages.", 500)


@router.post("/{session_id}/messages", response_model=ChatMessageResponse)
async def create_chat_message(session_id: str, request: ChatMessageCreateRequest):
    """Persist user message and return generated assistant answer."""
    service = get_chat_service()
    try:
        return await service.send_message(session_id=session_id, content=request.content)
    except ChatServiceError as exc:
        raise _typed_error(exc.code, exc.message, exc.status_code)
    except Exception:
        logger.exception("Failed to create chat message", extra={"session_id": session_id})
        raise _typed_error("CHAT_MESSAGE_CREATE_FAILED", "Failed to create chat message.", 500)


@router.get("/{session_id}/stream")
async def stream_chat_message(
    session_id: str,
    question: str = Query(..., min_length=1, max_length=8000),
):
    """Stream chat answer via server-sent events."""
    service = get_chat_service()

    async def event_stream():
        try:
            async for chunk in service.stream_message(session_id=session_id, content=question):
                yield chunk
        except ChatServiceError as exc:
            yield _format_sse("error", {"code": exc.code, "message": exc.message})
        except Exception:
            logger.exception("Failed to stream chat message", extra={"session_id": session_id})
            yield _format_sse(
                "error",
                {"code": "CHAT_STREAM_FAILED", "message": "Failed to stream chat response."},
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{session_id}/export")
async def export_chat_transcript(
    session_id: str,
    format: ChatExportFormat = Query(default=ChatExportFormat.MARKDOWN),
):
    """Export session transcript as markdown or JSON."""
    service = get_chat_service()
    try:
        filename, media_type, content = await service.export_transcript(session_id=session_id, fmt=format)
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ChatServiceError as exc:
        raise _typed_error(exc.code, exc.message, exc.status_code)
    except Exception:
        logger.exception("Failed to export chat transcript", extra={"session_id": session_id})
        raise _typed_error("CHAT_EXPORT_FAILED", "Failed to export chat transcript.", 500)
