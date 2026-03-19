"""Pydantic models for API request/response schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime


class JobStatus(str, Enum):
    """Podcast generation job status."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING_SCRIPT = "generating_script"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


# Repository Schemas

class AnalyzeRequest(BaseModel):
    """Request to analyze a GitHub repository."""
    url: str = Field(..., description="GitHub repository URL")


class AnalyzeResponse(BaseModel):
    """Response after repository analysis."""
    repo_id: str
    name: str
    description: Optional[str] = None
    default_branch: str = "main"
    file_count: int


class FileNode(BaseModel):
    """A node in the file tree (file or directory)."""
    name: str
    path: str
    is_dir: bool
    children: Optional[list["FileNode"]] = None


class FileTreeResponse(BaseModel):
    """File tree structure response."""
    repo_id: str
    root: FileNode


# Podcast Schemas

class CreatePodcastRequest(BaseModel):
    """Request to create a podcast."""
    repo_id: str
    selected_files: list[str] = Field(default_factory=list)
    title: Optional[str] = None
    learning_preferences: Optional[str] = None


class CreatePodcastResponse(BaseModel):
    """Response after starting podcast creation."""
    podcast_id: str
    status: JobStatus
    message: str


class PodcastStatusResponse(BaseModel):
    """Podcast generation status."""
    podcast_id: str
    status: JobStatus
    progress: float = Field(..., ge=0, le=100)
    current_step: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Chapter(BaseModel):
    """A chapter in the podcast."""
    id: int
    title: str
    start_time: float  # seconds
    end_time: float  # seconds
    description: Optional[str] = None


class ChapterListResponse(BaseModel):
    """List of chapters for a podcast."""
    podcast_id: str
    chapters: list[Chapter]


# Script Schemas

class ScriptSection(BaseModel):
    """A section of the generated script."""
    chapter_id: int
    title: str
    content: str
    estimated_duration: float  # seconds


class GeneratedScript(BaseModel):
    """Complete generated script with chapters."""
    repo_name: str
    title: str
    introduction: str
    sections: list[ScriptSection]
    conclusion: str
    total_estimated_duration: float
