"""Unit tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    FileNode,
    FileTreeResponse,
    CreatePodcastRequest,
    CreatePodcastResponse,
    PodcastStatusResponse,
    Chapter,
    ChapterListResponse,
    ScriptSection,
    GeneratedScript,
    JobStatus,
)


class TestAnalyzeRequest:
    """Tests for AnalyzeRequest schema."""

    def test_valid_url_accepted(self):
        """Valid URLs should be accepted."""
        request = AnalyzeRequest(url="https://github.com/user/repo")
        assert request.url == "https://github.com/user/repo"

    def test_empty_url_rejected(self):
        """Empty URL should be rejected."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(url="")

    def test_any_url_accepted(self):
        """Any non-empty URL string is accepted (validation is in service layer)."""
        request = AnalyzeRequest(url="not-a-url")
        assert request.url == "not-a-url"


class TestAnalyzeResponse:
    """Tests for AnalyzeResponse schema."""

    def test_valid_response(self):
        """Valid response should be accepted."""
        response = AnalyzeResponse(
            repo_id="abc123",
            name="test-repo",
            description="Test description",
            file_count=10,
        )
        assert response.repo_id == "abc123"
        assert response.name == "test-repo"
        assert response.file_count == 10

    def test_optional_description(self):
        """Description is optional."""
        response = AnalyzeResponse(
            repo_id="abc123",
            name="test-repo",
            file_count=10,
        )
        assert response.description is None

    def test_default_branch(self):
        """Default branch should default to 'main'."""
        response = AnalyzeResponse(
            repo_id="abc123",
            name="test-repo",
            file_count=10,
        )
        assert response.default_branch == "main"


class TestFileNode:
    """Tests for FileNode schema."""

    def test_file_node(self):
        """File node should be created correctly."""
        node = FileNode(
            name="test.py",
            path="test.py",
            is_dir=False,
        )
        assert node.name == "test.py"
        assert node.is_dir is False
        assert node.children is None

    def test_directory_node(self):
        """Directory node with children should work."""
        child = FileNode(name="child.py", path="dir/child.py", is_dir=False)
        parent = FileNode(
            name="dir",
            path="dir",
            is_dir=True,
            children=[child],
        )
        assert parent.is_dir is True
        assert len(parent.children) == 1

    def test_nested_file_tree(self):
        """Nested file tree structure should work."""
        leaf1 = FileNode(name="a.py", path="src/a.py", is_dir=False)
        leaf2 = FileNode(name="b.py", path="src/b.py", is_dir=False)
        src_dir = FileNode(
            name="src",
            path="src",
            is_dir=True,
            children=[leaf1, leaf2],
        )
        root = FileNode(
            name="root",
            path=".",
            is_dir=True,
            children=[src_dir],
        )
        assert len(root.children) == 1
        assert len(root.children[0].children) == 2


class TestFileTreeResponse:
    """Tests for FileTreeResponse schema."""

    def test_valid_response(self):
        """Valid response should be accepted."""
        root = FileNode(name="root", path=".", is_dir=True)
        response = FileTreeResponse(repo_id="abc123", root=root)
        assert response.repo_id == "abc123"
        assert response.root.name == "root"


class TestCreatePodcastRequest:
    """Tests for CreatePodcastRequest schema."""

    def test_valid_request(self):
        """Valid request should be accepted."""
        request = CreatePodcastRequest(
            repo_id="abc123",
            selected_files=["main.py", "src/utils.py"],
        )
        assert request.repo_id == "abc123"
        assert len(request.selected_files) == 2

    def test_empty_selected_files(self):
        """Empty selected files list should be allowed."""
        request = CreatePodcastRequest(repo_id="abc123")
        assert request.selected_files == []

    def test_optional_title(self):
        """Title is optional."""
        request = CreatePodcastRequest(repo_id="abc123")
        assert request.title is None


class TestPodcastStatusResponse:
    """Tests for PodcastStatusResponse schema."""

    def test_progress_range_validation(self):
        """Progress should be validated to be between 0 and 100."""
        from datetime import datetime

        now = datetime.utcnow()
        # Valid progress
        response = PodcastStatusResponse(
            podcast_id="abc123",
            status=JobStatus.PENDING,
            progress=50.0,
            created_at=now,
            updated_at=now,
        )
        assert response.progress == 50.0

    def test_progress_at_boundaries(self):
        """Progress at boundaries (0 and 100) should be valid."""
        from datetime import datetime

        now = datetime.utcnow()
        response_min = PodcastStatusResponse(
            podcast_id="abc123",
            status=JobStatus.PENDING,
            progress=0.0,
            created_at=now,
            updated_at=now,
        )
        assert response_min.progress == 0.0

        response_max = PodcastStatusResponse(
            podcast_id="abc123",
            status=JobStatus.COMPLETED,
            progress=100.0,
            created_at=now,
            updated_at=now,
        )
        assert response_max.progress == 100.0

    def test_optional_fields(self):
        """Optional fields should be handled correctly."""
        from datetime import datetime

        now = datetime.utcnow()
        response = PodcastStatusResponse(
            podcast_id="abc123",
            status=JobStatus.PENDING,
            progress=0.0,
            created_at=now,
            updated_at=now,
        )
        assert response.current_step is None
        assert response.error is None


class TestChapter:
    """Tests for Chapter schema."""

    def test_valid_chapter(self):
        """Valid chapter should be accepted."""
        chapter = Chapter(
            id=1,
            title="Introduction",
            start_time=0.0,
            end_time=60.0,
        )
        assert chapter.id == 1
        assert chapter.start_time == 0.0
        assert chapter.end_time == 60.0

    def test_optional_description(self):
        """Description is optional."""
        chapter = Chapter(
            id=1,
            title="Test",
            start_time=0.0,
            end_time=30.0,
        )
        assert chapter.description is None


class TestChapterListResponse:
    """Tests for ChapterListResponse schema."""

    def test_valid_response(self):
        """Valid response should be accepted."""
        chapters = [
            Chapter(id=1, title="Intro", start_time=0.0, end_time=60.0),
            Chapter(id=2, title="Main", start_time=60.0, end_time=120.0),
        ]
        response = ChapterListResponse(podcast_id="abc123", chapters=chapters)
        assert len(response.chapters) == 2


class TestScriptSection:
    """Tests for ScriptSection schema."""

    def test_valid_section(self):
        """Valid section should be accepted."""
        section = ScriptSection(
            chapter_id=1,
            title="Introduction",
            content="This is the content.",
            estimated_duration=60.0,
        )
        assert section.chapter_id == 1
        assert section.estimated_duration == 60.0


class TestGeneratedScript:
    """Tests for GeneratedScript schema."""

    def test_valid_script(self):
        """Valid script should be accepted."""
        section = ScriptSection(
            chapter_id=1,
            title="Chapter 1",
            content="Content",
            estimated_duration=60.0,
        )
        script = GeneratedScript(
            repo_name="test-repo",
            title="Understanding test-repo",
            introduction="Welcome",
            sections=[section],
            conclusion="Thank you",
            total_estimated_duration=120.0,
        )
        assert script.repo_name == "test-repo"
        assert len(script.sections) == 1


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_all_statuses_exist(self):
        """All expected statuses should exist."""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.ANALYZING == "analyzing"
        assert JobStatus.GENERATING_SCRIPT == "generating_script"
        assert JobStatus.SYNTHESIZING == "synthesizing"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"

    def test_status_is_string_enum(self):
        """JobStatus should be a string enum."""
        assert isinstance(JobStatus.PENDING, str)
        assert JobStatus.PENDING.value == "pending"
