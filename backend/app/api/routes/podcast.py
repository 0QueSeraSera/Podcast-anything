"""Podcast generation endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import (
    CreatePodcastRequest,
    CreatePodcastResponse,
    PodcastStatusResponse,
    ChapterListResponse,
)
from app.services.podcast_service import get_podcast_service

router = APIRouter()


@router.post("/create", response_model=CreatePodcastResponse)
async def create_podcast(request: CreatePodcastRequest):
    """
    Start a podcast generation job.

    Accepts repository ID and selected files/folders.
    """
    service = get_podcast_service()
    try:
        result = await service.create_podcast(
            repo_id=request.repo_id,
            selected_files=request.selected_files,
            title=request.title,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Podcast creation failed: {str(e)}")


@router.get("/{podcast_id}/status", response_model=PodcastStatusResponse)
async def get_podcast_status(podcast_id: str):
    """
    Check the status of a podcast generation job.
    """
    service = get_podcast_service()
    result = await service.get_status(podcast_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return result


@router.get("/{podcast_id}/audio")
async def get_podcast_audio(podcast_id: str):
    """
    Stream or download the generated audio file.
    """
    service = get_podcast_service()
    audio_path = await service.get_audio_path(podcast_id)
    if audio_path is None:
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
    chapters = await service.get_chapters(podcast_id)
    if chapters is None:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return ChapterListResponse(podcast_id=podcast_id, chapters=chapters)
