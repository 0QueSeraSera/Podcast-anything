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
    SavePodcastResponse,
    SavedPodcastListResponse,
)
from app.services.podcast_service import get_podcast_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create", response_model=CreatePodcastResponse, status_code=202)
async def create_podcast(request: CreatePodcastRequest):
    """
    Queue a podcast generation job and return immediately.

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
    suffix = audio_path.suffix.lower()
    media_type = "audio/wav" if suffix == ".wav" else "audio/mpeg"
    filename_ext = "wav" if suffix == ".wav" else "mp3"
    return FileResponse(
        path=audio_path,
        media_type=media_type,
        filename=f"podcast-{podcast_id}.{filename_ext}",
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


@router.post("/{podcast_id}/save", response_model=SavePodcastResponse)
async def save_podcast(podcast_id: str):
    """
    Save podcast artifacts (audio, script, metadata) to local library at ~/.podcast_anything.
    """
    service = get_podcast_service()
    start_time = time.monotonic()
    logger.info("POST /podcast/{podcast_id}/save received", extra={"podcast_id": podcast_id})
    try:
        result = await service.save_podcast(podcast_id)
        logger.info(
            "POST /podcast/{podcast_id}/save completed",
            extra={
                "podcast_id": podcast_id,
                "saved_path": result.saved_path,
                "elapsed_seconds": round(time.monotonic() - start_time, 2),
            },
        )
        return result
    except ValueError as e:
        logger.warning(
            "POST /podcast/{podcast_id}/save rejected",
            extra={"podcast_id": podcast_id, "error": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(
            "POST /podcast/{podcast_id}/save failed",
            extra={"podcast_id": podcast_id},
        )
        raise HTTPException(status_code=500, detail=f"Failed to save podcast: {str(e)}")


@router.get("/saved", response_model=SavedPodcastListResponse)
async def list_saved_podcasts():
    """
    List all podcasts saved in local library.
    """
    service = get_podcast_service()
    logger.debug("GET /podcast/saved")
    return await service.list_saved_podcasts()


@router.get("/saved/{podcast_id}/audio")
async def get_saved_podcast_audio(podcast_id: str):
    """
    Stream or download audio from saved library.
    """
    service = get_podcast_service()
    logger.info("GET /podcast/saved/{podcast_id}/audio", extra={"podcast_id": podcast_id})
    audio_path = await service.get_saved_podcast_path(podcast_id, "audio")
    if audio_path is None:
        raise HTTPException(status_code=404, detail="Saved audio not found")
    suffix = audio_path.suffix.lower()
    media_type = "audio/wav" if suffix == ".wav" else "audio/mpeg"
    filename_ext = "wav" if suffix == ".wav" else "mp3"
    return FileResponse(
        path=audio_path,
        media_type=media_type,
        filename=f"podcast-{podcast_id}.{filename_ext}",
    )


@router.get("/saved/{podcast_id}/script")
async def get_saved_podcast_script(podcast_id: str):
    """
    Get script from saved library.
    """
    service = get_podcast_service()
    logger.debug("GET /podcast/saved/{podcast_id}/script", extra={"podcast_id": podcast_id})
    script_path = await service.get_saved_podcast_path(podcast_id, "script")
    if script_path is None:
        raise HTTPException(status_code=404, detail="Saved script not found")
    return FileResponse(
        path=script_path,
        media_type="text/markdown",
        filename=f"podcast-{podcast_id}-script.md",
    )
