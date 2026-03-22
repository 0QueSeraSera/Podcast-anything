"""Main podcast orchestration service."""

import asyncio
import base64
import json
import logging
import shutil
import time
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
    GeneratedScript,
    JobStatus,
    Chapter,
    SavePodcastResponse,
    SavedPodcastMetadata,
    SavedPodcastListResponse,
)

settings = get_settings()
logger = logging.getLogger(__name__)

# Global singleton instance
_podcast_service_instance: Optional["PodcastService"] = None


def get_podcast_service() -> "PodcastService":
    """Get the singleton PodcastService instance."""
    global _podcast_service_instance
    if _podcast_service_instance is None:
        _podcast_service_instance = PodcastService()
    return _podcast_service_instance


class PodcastService:
    """Orchestrates the podcast generation pipeline."""

    def __init__(self):
        self.repos: dict = {}  # In-memory storage (use Redis/DB in production)
        self.podcasts: dict = {}  # In-memory storage
        self.repo_analyzer = RepoAnalyzer()
        self.script_generator = ScriptGenerator()
        self.audio_processor: Optional[AudioProcessor] = None

    async def analyze_repository(self, url: str) -> AnalyzeResponse:
        """Clone a GitHub repository and extract file tree metadata locally."""
        start_time = time.monotonic()
        logger.info("Analyze repository request received", extra={"url": url})
        # Validate URL
        parsed = urlparse(url)
        if not parsed.netloc == "github.com":
            logger.warning("Rejected non-GitHub URL", extra={"url": url})
            raise ValueError("Only GitHub repositories are supported")

        # Generate repo ID
        repo_id = str(uuid.uuid4())[:8]

        if settings.e2e_mock_pipeline:
            return await self._analyze_repository_mock(url=url, repo_id=repo_id)

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
        logger.info(
            "Repository analysis completed",
            extra={
                "repo_id": repo_id,
                "url": url,
                "repo_name": analysis["name"],
                "file_count": analysis["file_count"],
                "elapsed_seconds": round(time.monotonic() - start_time, 2),
            },
        )

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
        learning_preferences: Optional[str] = None,
    ) -> CreatePodcastResponse:
        """Start podcast generation."""
        start_time = time.monotonic()
        repo = self.repos.get(repo_id)
        if not repo:
            logger.warning("Create podcast failed: repository not found", extra={"repo_id": repo_id})
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
            "learning_preferences": learning_preferences,
        }
        logger.info(
            "Podcast generation requested",
            extra={
                "podcast_id": podcast_id,
                "repo_id": repo_id,
                "repo_name": repo["name"],
                "selected_files_count": len(selected_files),
                "has_learning_preferences": bool(learning_preferences and learning_preferences.strip()),
                "processing_mode": "synchronous",
            },
        )

        # Start async generation (in production, use Celery)
        # For now, we'll process synchronously
        if settings.e2e_mock_pipeline:
            await self._generate_podcast_mock(podcast_id)
        else:
            await self._generate_podcast(podcast_id)
        logger.info(
            "Create podcast request finished",
            extra={
                "podcast_id": podcast_id,
                "repo_id": repo_id,
                "final_status": str(self.podcasts[podcast_id]["status"]),
                "elapsed_seconds": round(time.monotonic() - start_time, 2),
            },
        )

        return CreatePodcastResponse(
            podcast_id=podcast_id,
            status=JobStatus.PENDING,
            message="Podcast generation started",
        )

    async def _generate_podcast(self, podcast_id: str):
        """Generate the podcast (internal method)."""
        start_time = time.monotonic()
        podcast = self.podcasts[podcast_id]
        repo = self.repos[podcast["repo_id"]]
        repo_path = Path(repo["path"])
        logger.info(
            "Podcast pipeline started",
            extra={
                "podcast_id": podcast_id,
                "repo_id": podcast["repo_id"],
                "repo_name": repo["name"],
                "repo_path": str(repo_path),
            },
        )

        try:
            # Update status
            self._update_status(podcast_id, JobStatus.GENERATING_SCRIPT, 10)

            # Generate script
            script_start = time.monotonic()
            script = await self.script_generator.generate(
                repo_path=repo_path,
                repo_name=repo["name"],
                selected_files=podcast["selected_files"],
                learning_preferences=podcast.get("learning_preferences"),
            )
            raw_output_path = self.script_generator.claude_client.last_output_path
            if raw_output_path:
                podcast["script_output_path"] = str(raw_output_path)

            logger.info(
                "Script generation stage completed",
                extra={
                    "podcast_id": podcast_id,
                    "sections": len(script.sections),
                    "elapsed_seconds": round(time.monotonic() - script_start, 2),
                },
            )

            if settings.e2e_skip_tts:
                self._complete_without_tts(podcast_id=podcast_id, script=script)
                logger.info(
                    "Podcast pipeline completed with TTS skipped",
                    extra={
                        "podcast_id": podcast_id,
                        "elapsed_seconds": round(time.monotonic() - start_time, 2),
                    },
                )
                return

            self._update_status(podcast_id, JobStatus.SYNTHESIZING, 40)

            # Generate audio
            if self.audio_processor is None:
                self.audio_processor = AudioProcessor()
                logger.info("AudioProcessor initialized", extra={"podcast_id": podcast_id})
            audio_start = time.monotonic()
            audio_result = await self.audio_processor.synthesize(
                script=script,
                output_dir=Path(settings.audio_output_dir),
                podcast_id=podcast_id,
                on_progress=lambda p: self._update_status(
                    podcast_id, JobStatus.SYNTHESIZING, 40 + p * 0.5
                ),
            )
            logger.info(
                "Audio synthesis stage completed",
                extra={
                    "podcast_id": podcast_id,
                    "audio_path": str(audio_result["audio_path"]),
                    "chapters": len(audio_result["chapters"]),
                    "duration_seconds": round(audio_result["duration"], 2),
                    "elapsed_seconds": round(time.monotonic() - audio_start, 2),
                },
            )

            # Store results
            podcast["audio_path"] = str(audio_result["audio_path"])
            podcast["chapters"] = audio_result["chapters"]
            podcast["duration"] = audio_result["duration"]

            self._update_status(podcast_id, JobStatus.COMPLETED, 100)
            logger.info(
                "Podcast pipeline completed",
                extra={
                    "podcast_id": podcast_id,
                    "elapsed_seconds": round(time.monotonic() - start_time, 2),
                },
            )

        except Exception as e:
            self._update_status(podcast_id, JobStatus.FAILED, 0, str(e))
            logger.exception(
                "Podcast pipeline failed",
                extra={
                    "podcast_id": podcast_id,
                    "repo_id": podcast["repo_id"],
                    "elapsed_seconds": round(time.monotonic() - start_time, 2),
                },
            )

    async def _analyze_repository_mock(self, url: str, repo_id: str) -> AnalyzeResponse:
        """Return deterministic repo metadata for full-stack E2E runs."""
        start_time = time.monotonic()
        repo_name = self._extract_repo_name(url)
        repo_path = Path(settings.temp_dir) / "e2e-repos" / repo_id
        repo_path.mkdir(parents=True, exist_ok=True)

        # Materialize a minimal file set so selected paths are realistic.
        (repo_path / "README.md").write_text(f"# {repo_name}\n", encoding="utf-8")
        src_dir = repo_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "main.py").write_text("print('hello from e2e')\n", encoding="utf-8")
        (src_dir / "utils.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

        file_tree = {
            "name": repo_name,
            "path": ".",
            "is_dir": True,
            "children": [
                {"name": "README.md", "path": "README.md", "is_dir": False},
                {
                    "name": "src",
                    "path": "src",
                    "is_dir": True,
                    "children": [
                        {"name": "main.py", "path": "src/main.py", "is_dir": False},
                        {"name": "utils.py", "path": "src/utils.py", "is_dir": False},
                    ],
                },
            ],
        }

        self.repos[repo_id] = {
            "url": url,
            "path": str(repo_path),
            "name": repo_name,
            "description": "Deterministic repository fixture for full-stack E2E tests",
            "file_count": 3,
            "file_tree": file_tree,
        }
        logger.info(
            "Repository analysis completed in E2E mock mode",
            extra={
                "repo_id": repo_id,
                "url": url,
                "repo_name": repo_name,
                "elapsed_seconds": round(time.monotonic() - start_time, 2),
            },
        )

        return AnalyzeResponse(
            repo_id=repo_id,
            name=repo_name,
            description="Deterministic repository fixture for full-stack E2E tests",
            file_count=3,
        )

    async def _generate_podcast_mock(self, podcast_id: str):
        """Generate deterministic podcast artifacts for full-stack E2E runs."""
        podcast = self.podcasts[podcast_id]

        self._update_status(podcast_id, JobStatus.GENERATING_SCRIPT, 20)
        await asyncio.sleep(0.05)

        self._update_status(podcast_id, JobStatus.SYNTHESIZING, 60)
        await asyncio.sleep(0.05)

        output_dir = Path(settings.audio_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / f"{podcast_id}.mp3"
        audio_path.write_bytes(self._mock_mp3_bytes())

        podcast["audio_path"] = str(audio_path)
        podcast["chapters"] = [
            Chapter(id=1, title="Introduction", start_time=0.0, end_time=10.0),
            Chapter(id=2, title="Core Concepts", start_time=10.0, end_time=30.0),
            Chapter(id=3, title="Wrap Up", start_time=30.0, end_time=45.0),
        ]
        podcast["duration"] = 45.0

        self._update_status(podcast_id, JobStatus.COMPLETED, 100)

    def _complete_without_tts(self, podcast_id: str, script: GeneratedScript):
        """Mark podcast complete using script-only chapter metadata."""
        podcast = self.podcasts[podcast_id]
        chapters = self._build_chapters_from_script(script)
        podcast["chapters"] = chapters
        podcast["duration"] = script.total_estimated_duration
        podcast["audio_path"] = None
        self._update_status(podcast_id, JobStatus.COMPLETED, 100)

    @staticmethod
    def _build_chapters_from_script(script: GeneratedScript) -> list[Chapter]:
        """Build chapter metadata directly from generated script sections."""
        chapters: list[Chapter] = []
        current = 0.0
        for idx, section in enumerate(script.sections, start=1):
            duration = max(float(section.estimated_duration), 1.0)
            chapters.append(
                Chapter(
                    id=idx,
                    title=section.title,
                    start_time=round(current, 2),
                    end_time=round(current + duration, 2),
                )
            )
            current += duration
        return chapters

    @staticmethod
    def _extract_repo_name(url: str) -> str:
        """Extract repository name from URL."""
        path = urlparse(url).path.strip("/")
        if not path:
            return "repository"
        return path.split("/")[-1] or "repository"

    @staticmethod
    def _mock_mp3_bytes() -> bytes:
        """Return a tiny deterministic MP3 payload for browser playback."""
        # Small silent MP3 frame sequence, base64 encoded.
        return base64.b64decode(
            "SUQzAwAAAAAAFlRFTkMAAAAMAAADTGF2ZjU2LjQwLjEwMQAAAAAAAAAAAAAA//uQxAADBzQATKxAAAAAAAABAAACcQCA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

    def _update_status(
        self,
        podcast_id: str,
        status: JobStatus,
        progress: float,
        error: Optional[str] = None,
    ):
        """Update podcast status."""
        podcast = self.podcasts[podcast_id]
        previous_status = podcast.get("status")
        podcast["status"] = status
        podcast["progress"] = progress
        podcast["updated_at"] = datetime.utcnow()
        podcast["current_step"] = status.value.replace("_", " ").title()
        if error:
            podcast["error"] = error
        if previous_status != status:
            logger.info(
                "Podcast status transitioned",
                extra={
                    "podcast_id": podcast_id,
                    "from_status": str(previous_status),
                    "to_status": str(status),
                    "progress": round(progress, 1),
                    "error": error,
                },
            )
        else:
            logger.debug(
                "Podcast progress updated",
                extra={
                    "podcast_id": podcast_id,
                    "status": str(status),
                    "progress": round(progress, 1),
                },
            )

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
        audio_path = podcast.get("audio_path")
        if not audio_path:
            return None
        return Path(audio_path)

    async def get_script_content(self, podcast_id: str) -> Optional[dict]:
        """Get persisted Claude CLI script output for a podcast."""
        podcast = self.podcasts.get(podcast_id)
        if not podcast:
            return None

        script_output_path = podcast.get("script_output_path")
        if not script_output_path:
            return None

        path = Path(script_output_path)
        if not path.exists():
            return None

        return {
            "source_path": str(path),
            "content": path.read_text(encoding="utf-8"),
        }

    async def get_chapters(self, podcast_id: str) -> Optional[list[Chapter]]:
        """Get chapters for a podcast."""
        podcast = self.podcasts.get(podcast_id)
        if not podcast:
            return None
        return podcast.get("chapters", [])

    def _get_library_dir(self) -> Path:
        """Get the local library directory path."""
        return Path.home() / ".podcast_anything"

    async def save_podcast(self, podcast_id: str) -> SavePodcastResponse:
        """Save podcast artifacts to local library at ~/.podcast_anything."""
        start_time = time.monotonic()
        podcast = self.podcasts.get(podcast_id)
        if not podcast:
            logger.warning("Save podcast failed: podcast not found", extra={"podcast_id": podcast_id})
            raise ValueError("Podcast not found")

        if podcast["status"] != JobStatus.COMPLETED:
            logger.warning(
                "Save podcast failed: podcast not completed",
                extra={"podcast_id": podcast_id, "status": str(podcast["status"])},
            )
            raise ValueError("Podcast is not completed yet")

        library_dir = self._get_library_dir()
        podcast_dir = library_dir / podcast_id
        podcast_dir.mkdir(parents=True, exist_ok=True)

        audio_saved = False
        script_saved = False
        metadata_saved = False

        # Save audio file
        audio_path = podcast.get("audio_path")
        if audio_path:
            src_audio = Path(audio_path)
            if src_audio.exists():
                dst_audio = podcast_dir / f"audio{src_audio.suffix}"
                shutil.copy2(src_audio, dst_audio)
                audio_saved = True
                logger.debug(
                    "Audio file saved to library",
                    extra={"podcast_id": podcast_id, "dst_path": str(dst_audio)},
                )

        # Save script file
        script_path = podcast.get("script_output_path")
        if script_path:
            src_script = Path(script_path)
            if src_script.exists():
                dst_script = podcast_dir / "script.md"
                shutil.copy2(src_script, dst_script)
                script_saved = True
                logger.debug(
                    "Script file saved to library",
                    extra={"podcast_id": podcast_id, "dst_path": str(dst_script)},
                )

        # Save metadata
        repo = self.repos.get(podcast["repo_id"], {})
        metadata = {
            "podcast_id": podcast_id,
            "title": podcast.get("title", "Untitled Podcast"),
            "repo_name": repo.get("name"),
            "created_at": podcast["created_at"].isoformat(),
            "saved_at": datetime.utcnow().isoformat(),
            "duration": podcast.get("duration"),
            "chapters": [c.model_dump() for c in podcast.get("chapters", [])],
        }
        metadata_path = podcast_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        metadata_saved = True

        logger.info(
            "Podcast saved to local library",
            extra={
                "podcast_id": podcast_id,
                "saved_path": str(podcast_dir),
                "audio_saved": audio_saved,
                "script_saved": script_saved,
                "metadata_saved": metadata_saved,
                "elapsed_seconds": round(time.monotonic() - start_time, 2),
            },
        )

        return SavePodcastResponse(
            podcast_id=podcast_id,
            saved_path=str(podcast_dir),
            audio_saved=audio_saved,
            script_saved=script_saved,
            metadata_saved=metadata_saved,
        )

    async def list_saved_podcasts(self) -> SavedPodcastListResponse:
        """List all podcasts saved in local library."""
        library_dir = self._get_library_dir()
        podcasts: list[SavedPodcastMetadata] = []

        if not library_dir.exists():
            return SavedPodcastListResponse(podcasts=podcasts)

        for podcast_dir in library_dir.iterdir():
            if not podcast_dir.is_dir():
                continue
            metadata_path = podcast_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                podcasts.append(
                    SavedPodcastMetadata(
                        podcast_id=data["podcast_id"],
                        title=data.get("title", "Untitled"),
                        repo_name=data.get("repo_name"),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        saved_at=datetime.fromisoformat(data["saved_at"]),
                        duration=data.get("duration"),
                        chapters=[Chapter(**c) for c in data.get("chapters", [])],
                    )
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(
                    "Failed to parse saved podcast metadata",
                    extra={"path": str(metadata_path), "error": str(e)},
                )

        # Sort by saved_at descending (most recent first)
        podcasts.sort(key=lambda p: p.saved_at, reverse=True)
        logger.debug("Listed saved podcasts", extra={"count": len(podcasts)})
        return SavedPodcastListResponse(podcasts=podcasts)

    async def get_saved_podcast_path(self, podcast_id: str, file_type: str) -> Optional[Path]:
        """Get path to a saved podcast file."""
        library_dir = self._get_library_dir()
        podcast_dir = library_dir / podcast_id
        if not podcast_dir.exists():
            return None

        if file_type == "audio":
            for ext in (".mp3", ".wav"):
                audio_path = podcast_dir / f"audio{ext}"
                if audio_path.exists():
                    return audio_path
            return None
        elif file_type == "script":
            script_path = podcast_dir / "script.md"
            return script_path if script_path.exists() else None
        elif file_type == "metadata":
            metadata_path = podcast_dir / "metadata.json"
            return metadata_path if metadata_path.exists() else None
        return None
