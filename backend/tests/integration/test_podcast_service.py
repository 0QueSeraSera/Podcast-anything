"""Integration tests for PodcastService orchestration."""

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import JobStatus
from app.services.podcast_service import PodcastService, get_podcast_service


@pytest.fixture
def clean_service():
    """Reset the singleton before and after each test."""
    # Reset before
    import app.services.podcast_service as ps_module
    ps_module._podcast_service_instance = None

    yield

    # Reset after
    ps_module._podcast_service_instance = None


@pytest.fixture
def mock_repo_analyzer():
    """Create a mock RepoAnalyzer."""
    analyzer = MagicMock()

    async def mock_clone(url, repo_id):
        tmp_dir = Path(tempfile.mkdtemp(prefix=f"mock_repo_{repo_id}_"))
        (tmp_dir / "README.md").write_text("# Test Repo")
        (tmp_dir / "main.py").write_text("print('hello')")
        return tmp_dir

    async def mock_analyze(path):
        return {
            "name": "test-repo",
            "description": "A test repository",
            "file_count": 2,
            "file_tree": {
                "name": "test-repo",
                "path": ".",
                "is_dir": True,
                "children": [
                    {"name": "README.md", "path": "README.md", "is_dir": False},
                    {"name": "main.py", "path": "main.py", "is_dir": False},
                ],
            },
        }

    analyzer.clone = AsyncMock(side_effect=mock_clone)
    analyzer.analyze = AsyncMock(side_effect=mock_analyze)

    return analyzer


@pytest.fixture
def mock_script_generator():
    """Create a mock ScriptGenerator."""
    from app.models.schemas import GeneratedScript, ScriptSection

    generator = MagicMock()

    async def mock_generate(
        repo_path,
        repo_name,
        selected_files,
        learning_preferences=None,
    ):
        return GeneratedScript(
            repo_name=repo_name,
            title=f"Understanding {repo_name}",
            introduction="Welcome to this podcast.",
            sections=[
                ScriptSection(
                    chapter_id=1,
                    title="Main Content",
                    content="This is the main content.",
                    estimated_duration=60.0,
                ),
            ],
            conclusion="Thank you for listening.",
            total_estimated_duration=120.0,
        )

    generator.generate = AsyncMock(side_effect=mock_generate)

    return generator


@pytest.fixture
def mock_audio_processor():
    """Create a mock AudioProcessor."""
    from app.models.schemas import Chapter

    processor = MagicMock()

    async def mock_synthesize(script, output_dir, podcast_id, on_progress=None):
        # Create a dummy audio file
        audio_path = output_dir / f"{podcast_id}.mp3"
        audio_path.write_bytes(b"MOCK_AUDIO_DATA")

        if on_progress:
            on_progress(0.5)
            on_progress(1.0)

        return {
            "audio_path": str(audio_path),
            "chapters": [
                Chapter(id=1, title="Introduction", start_time=0.0, end_time=30.0),
                Chapter(id=2, title="Main Content", start_time=30.0, end_time=90.0),
                Chapter(id=3, title="Conclusion", start_time=90.0, end_time=120.0),
            ],
            "duration": 120.0,
        }

    processor.synthesize = AsyncMock(side_effect=mock_synthesize)

    return processor


class TestPodcastServiceAnalyzeRepository:
    """Tests for analyze_repository method."""

    @pytest.mark.asyncio
    async def test_analyze_repository_success(self, mock_repo_analyzer):
        """Analyze repository should return correct info."""
        service = PodcastService.__new__(PodcastService)
        service.repos = {}
        service.podcasts = {}
        service.repo_analyzer = mock_repo_analyzer

        result = await service.analyze_repository("https://github.com/user/test-repo")

        assert result.repo_id is not None
        assert result.name == "test-repo"
        assert result.file_count == 2

    @pytest.mark.asyncio
    async def test_analyze_repository_stores_info(self, mock_repo_analyzer):
        """Analyze repository should store repo info."""
        service = PodcastService.__new__(PodcastService)
        service.repos = {}
        service.podcasts = {}
        service.repo_analyzer = mock_repo_analyzer

        result = await service.analyze_repository("https://github.com/user/test-repo")

        assert result.repo_id in service.repos
        assert service.repos[result.repo_id]["name"] == "test-repo"

    @pytest.mark.asyncio
    async def test_analyze_repository_rejects_non_github(self):
        """Analyze repository should reject non-GitHub URLs."""
        service = PodcastService.__new__(PodcastService)
        service.repos = {}
        service.podcasts = {}

        with pytest.raises(ValueError, match="Only GitHub repositories"):
            await service.analyze_repository("https://gitlab.com/user/repo")


class TestPodcastServiceGetFileTree:
    """Tests for get_file_tree method."""

    @pytest.mark.asyncio
    async def test_get_file_tree_success(self):
        """Get file tree should return tree structure."""
        service = PodcastService.__new__(PodcastService)
        service.repos = {
            "test1234": {
                "file_tree": {
                    "name": "root",
                    "path": ".",
                    "is_dir": True,
                    "children": [],
                }
            }
        }

        result = await service.get_file_tree("test1234")

        assert result is not None
        assert result.repo_id == "test1234"

    @pytest.mark.asyncio
    async def test_get_file_tree_not_found(self):
        """Get file tree should return None for unknown repo."""
        service = PodcastService.__new__(PodcastService)
        service.repos = {}

        result = await service.get_file_tree("unknown")

        assert result is None


class TestPodcastServiceCreatePodcast:
    """Tests for create_podcast method."""

    @pytest.mark.asyncio
    async def test_create_podcast_initializes_status(
        self, mock_repo_analyzer, mock_script_generator, mock_audio_processor
    ):
        """Create podcast should initialize status."""
        service = PodcastService.__new__(PodcastService)
        service.repos = {
            "test1234": {
                "name": "test-repo",
                "path": "/tmp/test",
                "url": "https://github.com/user/test-repo",
            }
        }
        service.podcasts = {}
        service.repo_analyzer = mock_repo_analyzer
        service.script_generator = mock_script_generator
        service.audio_processor = mock_audio_processor

        result = await service.create_podcast(
            repo_id="test1234",
            selected_files=["main.py"],
        )

        assert result.podcast_id is not None
        assert result.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_podcast_unknown_repo(self):
        """Create podcast should fail for unknown repo."""
        service = PodcastService.__new__(PodcastService)
        service.repos = {}
        service.podcasts = {}

        with pytest.raises(ValueError, match="Repository not found"):
            await service.create_podcast("unknown", [])

    @pytest.mark.asyncio
    async def test_create_podcast_returns_immediately_for_long_running_job(self):
        """Create podcast should return pending while background task keeps running."""
        service = PodcastService.__new__(PodcastService)
        service.repos = {
            "test1234": {
                "name": "test-repo",
                "path": "/tmp/test",
                "url": "https://github.com/user/test-repo",
            }
        }
        service.podcasts = {}
        service._generation_tasks = set()

        generation_started = asyncio.Event()
        generation_finished = asyncio.Event()

        async def slow_generation(podcast_id: str):
            generation_started.set()
            await asyncio.sleep(0.15)
            service._update_status(podcast_id, JobStatus.COMPLETED, 100)
            generation_finished.set()

        service._run_generation_task = slow_generation

        start = time.monotonic()
        result = await service.create_podcast(repo_id="test1234", selected_files=["main.py"])
        elapsed = time.monotonic() - start

        assert elapsed < 0.1
        assert result.status == JobStatus.PENDING
        assert service.podcasts[result.podcast_id]["status"] == JobStatus.PENDING

        await asyncio.wait_for(generation_started.wait(), timeout=0.3)
        await asyncio.wait_for(generation_finished.wait(), timeout=1.0)

        final_status = await service.get_status(result.podcast_id)
        assert final_status is not None
        assert final_status.status == JobStatus.COMPLETED


class TestPodcastServiceGetStatus:
    """Tests for get_status method."""

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """Get status should return podcast status."""
        from datetime import datetime

        now = datetime.utcnow()
        service = PodcastService.__new__(PodcastService)
        service.podcasts = {
            "pod1234": {
                "status": JobStatus.COMPLETED,
                "progress": 100.0,
                "created_at": now,
                "updated_at": now,
                "current_step": "Completed",
            }
        }

        result = await service.get_status("pod1234")

        assert result is not None
        assert result.status == JobStatus.COMPLETED
        assert result.progress == 100.0

    @pytest.mark.asyncio
    async def test_get_status_not_found(self):
        """Get status should return None for unknown podcast."""
        service = PodcastService.__new__(PodcastService)
        service.podcasts = {}

        result = await service.get_status("unknown")

        assert result is None


class TestPodcastServiceSingleton:
    """Tests for singleton behavior."""

    def test_singleton_returns_same_instance(self, clean_service):
        """Get podcast service should return same instance."""
        service1 = get_podcast_service()
        service2 = get_podcast_service()

        assert service1 is service2

    def test_singleton_persists_data(self, clean_service):
        """Singleton should persist data across calls."""
        service1 = get_podcast_service()
        service1.repos["test"] = {"name": "test-repo"}

        service2 = get_podcast_service()
        assert "test" in service2.repos


class TestPodcastServiceErrorPropagation:
    """Tests for error handling in podcast generation."""

    @pytest.mark.asyncio
    async def test_script_generation_error_propagates(self, mock_repo_analyzer, mock_audio_processor):
        """Script generation errors should be captured in status."""
        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(side_effect=Exception("Script generation failed"))

        service = PodcastService.__new__(PodcastService)
        service.repos = {
            "test1234": {
                "name": "test-repo",
                "path": "/tmp/test",
            }
        }
        service.podcasts = {}
        service.repo_analyzer = mock_repo_analyzer
        service.script_generator = mock_generator
        service.audio_processor = mock_audio_processor

        result = await service.create_podcast("test1234", [])

        for _ in range(50):
            podcast = service.podcasts[result.podcast_id]
            if podcast["status"] == JobStatus.FAILED:
                break
            await asyncio.sleep(0.01)

        assert podcast["status"] == JobStatus.FAILED
        assert "Script generation failed" in podcast.get("error", "")


class TestPodcastServiceChapters:
    """Tests for chapter retrieval."""

    @pytest.mark.asyncio
    async def test_get_chapters_success(self):
        """Get chapters should return chapter list."""
        from app.models.schemas import Chapter

        service = PodcastService.__new__(PodcastService)
        service.podcasts = {
            "pod1234": {
                "status": JobStatus.COMPLETED,
                "chapters": [
                    Chapter(id=1, title="Intro", start_time=0.0, end_time=60.0),
                    Chapter(id=2, title="Main", start_time=60.0, end_time=120.0),
                ],
            }
        }

        chapters = await service.get_chapters("pod1234")

        assert chapters is not None
        assert len(chapters) == 2

    @pytest.mark.asyncio
    async def test_get_chapters_not_found(self):
        """Get chapters should return None for unknown podcast."""
        service = PodcastService.__new__(PodcastService)
        service.podcasts = {}

        chapters = await service.get_chapters("unknown")

        assert chapters is None


class TestPodcastServiceScriptOutput:
    """Tests for persisted script output retrieval."""

    @pytest.mark.asyncio
    async def test_get_script_content_returns_persisted_output(self):
        """Script content endpoint data should come from stored file path."""
        script_path = Path(tempfile.mkdtemp()) / "script.md"
        script_path.write_text("# Test script", encoding="utf-8")

        service = PodcastService.__new__(PodcastService)
        service.podcasts = {
            "pod1234": {
                "script_output_path": str(script_path),
            }
        }

        result = await service.get_script_content("pod1234")

        assert result is not None
        assert result["source_path"] == str(script_path)
        assert result["content"] == "# Test script"
