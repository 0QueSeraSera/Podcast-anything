"""Repository analysis endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    FileTreeResponse,
)
from app.services.podcast_service import get_podcast_service

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest):
    """
    Clone a GitHub repository and register its basic metadata.

    Returns a repository ID and basic information for file tree browsing.
    """
    service = get_podcast_service()
    try:
        result = await service.analyze_repository(request.url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{repo_id}/structure", response_model=FileTreeResponse)
async def get_repository_structure(repo_id: str):
    """
    Get the file tree structure of an analyzed repository.

    Used for file/folder selection.
    """
    service = get_podcast_service()
    try:
        result = await service.get_file_tree(repo_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Repository not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get structure: {str(e)}")
