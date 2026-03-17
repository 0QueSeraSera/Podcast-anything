"""Main podcast orchestration service."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from app.config import get_settings
from app.core.repo_analyzer import RepoAnalyzer
from app.core.script_generator import ScriptGenerator
from app.core.audio_processor import AudioProcessor
from app.models.schemas import (
    AnalyzeResponse,
    FileTreeResponse,
    FileNode,
    CreatePodcastResponse,
    PodcastStatusResponse,
    JobStatus,
    Chapter,
)

settings = get_settings()


class PodcastService:
    """Orchestrates the podcast generation pipeline."""

    def __init__(self):
        self.repos: dict = {}  # In-memory storage (use Redis/DB in production)
        self.podcasts: dict = {}  # In-memory storage
        self.repo_analyzer = RepoAnalyzer()
        self.script_generator = ScriptGenerator()
        self.audio_processor = AudioProcessor()

    async def analyze_repository(self, url: str) -> AnalyzeResponse:
        """Clone and analyze a GitHub repository."""
        # Validate URL
        parsed = urlparse(url)
        if not parsed.netloc == "github.com":
            raise ValueError("Only GitHub repositories are supported")

        # Generate repo ID
        repo_id = str(uuid.uuid4())[:8]

        # Clone and analyze
        repo_path = await self.repo_analyzer.clone(url, repo_id)
        analysis = await self.repo_analyzer.analyze(repo_path)

        # Store repo info
        self.repos[repo_id] = {
            "url": url,
            "path": str(repo_path),
            "name": analysis["name"],
            "description": analysis.get("description"),
            "file_count": analysis["file_count"],
            "file_tree": analysis["file_tree"],
        }

        return AnalyzeResponse(
            repo_id=repo_id,
            name=analysis["name"],
            description=analysis.get("description"),
            file_count=analysis["file_count"],
        )

    async def get_file_tree(self, repo_id: str) -> Optional[FileTreeResponse]:
        """Get the file tree for a repository."""
        repo = self.repos.get(repo_id)
        if not repo:
            return None

        def build_tree(node: dict) -> FileNode:
            return FileNode(
                name=node["name"],
                path=node["path"],
                is_dir=node["is_dir"],
                children=[build_tree(c) for c in node.get("children", [])] if node["is_dir"] else None,
            )

        return FileTreeResponse(
            repo_id=repo_id,
            root=build_tree(repo["file_tree"]),
        )

    async def create_podcast(
        self,
        repo_id: str,
        selected_files: list[str],
        title: Optional[str] = None,
    ) -> CreatePodcastResponse:
        """Start podcast generation."""
        repo = self.repos.get(repo_id)
        if not repo:
            raise ValueError("Repository not found")

        podcast_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow()

        self.podcasts[podcast_id] = {
            "repo_id": repo_id,
            "status": JobStatus.PENDING,
            "progress": 0.0,
            "created_at": now,
            "updated_at": now,
            "selected_files": selected_files,
            "title": title or f"Understanding {repo['name']}",
        }

        # Start async generation (in production, use Celery)
        # For now, we'll process synchronously
        await self._generate_podcast(podcast_id)

        return CreatePodcastResponse(
            podcast_id=podcast_id,
            status=JobStatus.PENDING,
            message="Podcast generation started",
        )

    async def _generate_podcast(self, podcast_id: str):
        """Generate the podcast (internal method)."""
        podcast = self.podcasts[podcast_id]
        repo = self.repos[podcast["repo_id"]]
        repo_path = Path(repo["path"])

        try:
            # Update status
            self._update_status(podcast_id, JobStatus.GENERATING_SCRIPT, 10)

            # Generate script
            script = await self.script_generator.generate(
                repo_path=repo_path,
                repo_name=repo["name"],
                selected_files=podcast["selected_files"],
            )

            self._update_status(podcast_id, JobStatus.SYNTHESIZING, 40)

            # Generate audio
            audio_result = await self.audio_processor.synthesize(
                script=script,
                output_dir=Path(settings.audio_output_dir),
                podcast_id=podcast_id,
                on_progress=lambda p: self._update_status(
                    podcast_id, JobStatus.SYNTHESIZING, 40 + p * 0.5
                ),
            )

            # Store results
            podcast["audio_path"] = str(audio_result["audio_path"])
            podcast["chapters"] = audio_result["chapters"]
            podcast["duration"] = audio_result["duration"]

            self._update_status(podcast_id, JobStatus.COMPLETED, 100)

        except Exception as e:
            self._update_status(podcast_id, JobStatus.FAILED, 0, str(e))

    def _update_status(
        self,
        podcast_id: str,
        status: JobStatus,
        progress: float,
        error: Optional[str] = None,
    ):
        """Update podcast status."""
        podcast = self.podcasts[podcast_id]
        podcast["status"] = status
        podcast["progress"] = progress
        podcast["updated_at"] = datetime.utcnow()
        podcast["current_step"] = status.value.replace("_", " ").title()
        if error:
            podcast["error"] = error

    async def get_status(self, podcast_id: str) -> Optional[PodcastStatusResponse]:
        """Get podcast generation status."""
        podcast = self.podcasts.get(podcast_id)
        if not podcast:
            return None

        return PodcastStatusResponse(
            podcast_id=podcast_id,
            status=podcast["status"],
            progress=podcast["progress"],
            current_step=podcast.get("current_step"),
            error=podcast.get("error"),
            created_at=podcast["created_at"],
            updated_at=podcast["updated_at"],
        )

    async def get_audio_path(self, podcast_id: str) -> Optional[Path]:
        """Get the audio file path for a podcast."""
        podcast = self.podcasts.get(podcast_id)
        if not podcast or podcast["status"] != JobStatus.COMPLETED:
            return None
        return Path(podcast["audio_path"])

    async def get_chapters(self, podcast_id: str) -> Optional[list[Chapter]]:
        """Get chapters for a podcast."""
        podcast = self.podcasts.get(podcast_id)
        if not podcast:
            return None
        return podcast.get("chapters", [])
