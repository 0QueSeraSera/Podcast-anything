"""Podcast generation endpoints."""

import logging
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import (
    CreatePodcastRequest,
    CreatePodcastResponse,
    PodcastStatusResponse,
    ChapterListResponse,
    ScriptContentResponse,
)
from app.services.podcast_service import get_podcast_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create", response_model=CreatePodcastResponse)
async def create_podcast(request: CreatePodcastRequest):
    """
    Start a podcast generation job.

    Accepts repository ID and selected files/folders.
    """
    service = get_podcast_service()
    start_time = time.monotonic()
    logger.info(
        "POST /podcast/create received",
        extra={
            "repo_id": request.repo_id,
            "selected_files_count": len(request.selected_files),
        },
    )
    try:
        result = await service.create_podcast(
            repo_id=request.repo_id,
            selected_files=request.selected_files,
            title=request.title,
            learning_preferences=request.learning_preferences,
        )
        logger.info(
            "POST /podcast/create completed",
            extra={
                "repo_id": request.repo_id,
                "podcast_id": result.podcast_id,
                "status": result.status.value,
                "elapsed_seconds": round(time.monotonic() - start_time, 2),
            },
        )
        return result
    except ValueError as e:
        logger.warning(
            "POST /podcast/create rejected",
            extra={
                "repo_id": request.repo_id,
                "error": str(e),
                "elapsed_seconds": round(time.monotonic() - start_time, 2),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(
            "POST /podcast/create failed",
            extra={
                "repo_id": request.repo_id,
                "elapsed_seconds": round(time.monotonic() - start_time, 2),
            },
        )
        raise HTTPException(status_code=500, detail=f"Podcast creation failed: {str(e)}")


@router.get("/{podcast_id}/status", response_model=PodcastStatusResponse)
async def get_podcast_status(podcast_id: str):
    """
    Check the status of a podcast generation job.
    """
    service = get_podcast_service()
    logger.debug("GET /podcast/{podcast_id}/status", extra={"podcast_id": podcast_id})
    result = await service.get_status(podcast_id)
    if result is None:
        logger.warning("Podcast status not found", extra={"podcast_id": podcast_id})
        raise HTTPException(status_code=404, detail="Podcast not found")
    return result


@router.get("/{podcast_id}/audio")
async def get_podcast_audio(podcast_id: str):
    """
    Stream or download the generated audio file.
    """
    service = get_podcast_service()
    logger.info("GET /podcast/{podcast_id}/audio", extra={"podcast_id": podcast_id})
    audio_path = await service.get_audio_path(podcast_id)
    if audio_path is None:
        logger.warning("Podcast audio not ready", extra={"podcast_id": podcast_id})
        raise HTTPException(status_code=404, detail="Audio not found or not ready")
    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=f"podcast-{podcast_id}.mp3",
    )


@router.get("/{podcast_id}/chapters", response_model=ChapterListResponse)
async def get_podcast_chapters(podcast_id: str):
    """
    Get chapter metadata for the podcast.
    """
    service = get_podcast_service()
    logger.debug("GET /podcast/{podcast_id}/chapters", extra={"podcast_id": podcast_id})
    chapters = await service.get_chapters(podcast_id)
    if chapters is None:
        logger.warning("Podcast chapters not found", extra={"podcast_id": podcast_id})
        raise HTTPException(status_code=404, detail="Podcast not found")
    return ChapterListResponse(podcast_id=podcast_id, chapters=chapters)


@router.get("/{podcast_id}/script", response_model=ScriptContentResponse)
async def get_podcast_script(podcast_id: str):
    """
    Get raw Claude CLI script output for inspection/debugging.
    """
    service = get_podcast_service()
    script_result = await service.get_script_content(podcast_id)
    if script_result is None:
        raise HTTPException(status_code=404, detail="Script output not found")

    return ScriptContentResponse(
        podcast_id=podcast_id,
        source_path=script_result["source_path"],
        content=script_result["content"],
    )
