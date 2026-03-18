"""Integration tests for API routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.schemas import JobStatus


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_podcast_service():
    """Create a mock PodcastService."""
    from app.models.schemas import (
        AnalyzeResponse,
        FileTreeResponse,
        FileNode,
        CreatePodcastResponse,
        PodcastStatusResponse,
        Chapter,
    )
    from datetime import datetime

    service = MagicMock()

    # Mock analyze_repository
    service.analyze_repository = AsyncMock(
        return_value=AnalyzeResponse(
            repo_id="test1234",
            name="test-repo",
            description="A test repository",
            file_count=10,
        )
    )

    # Mock get_file_tree
    service.get_file_tree = AsyncMock(
        return_value=FileTreeResponse(
            repo_id="test1234",
            root=FileNode(
                name="root",
                path=".",
                is_dir=True,
                children=[
                    FileNode(name="main.py", path="main.py", is_dir=False),
                ],
            ),
        )
    )

    # Mock create_podcast
    service.create_podcast = AsyncMock(
        return_value=CreatePodcastResponse(
            podcast_id="pod1234",
            status=JobStatus.PENDING,
            message="Podcast generation started",
        )
    )

    # Mock get_status
    now = datetime.utcnow()
    service.get_status = AsyncMock(
        return_value=PodcastStatusResponse(
            podcast_id="pod1234",
            status=JobStatus.COMPLETED,
            progress=100.0,
            current_step="Completed",
            created_at=now,
            updated_at=now,
        )
    )

    # Mock get_chapters
    service.get_chapters = AsyncMock(
        return_value=[
            Chapter(id=1, title="Intro", start_time=0.0, end_time=60.0),
            Chapter(id=2, title="Main", start_time=60.0, end_time=120.0),
        ]
    )

    return service


class TestHealthRoutes:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    def test_readiness_check(self, client):
        """Readiness endpoint should check configuration."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "api_keys_configured" in data


class TestRepositoryRoutes:
    """Tests for repository endpoints."""

    @patch("app.api.routes.repository.get_podcast_service")
    def test_analyze_repository_success(self, mock_get_service, client, mock_podcast_service):
        """Analyze endpoint should return repository info."""
        mock_get_service.return_value = mock_podcast_service

        response = client.post(
            "/api/v1/repository/analyze",
            json={"url": "https://github.com/user/repo"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["repo_id"] == "test1234"
        assert data["name"] == "test-repo"

    @patch("app.api.routes.repository.get_podcast_service")
    def test_analyze_repository_invalid_url(self, mock_get_service, client):
        """Analyze endpoint should return 400 for invalid URL."""
        mock_service = MagicMock()
        mock_service.analyze_repository = AsyncMock(
            side_effect=ValueError("Only GitHub repositories are supported")
        )
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/repository/analyze",
            json={"url": "https://gitlab.com/user/repo"},
        )

        assert response.status_code == 400

    @patch("app.api.routes.repository.get_podcast_service")
    def test_get_repository_structure(self, mock_get_service, client, mock_podcast_service):
        """Structure endpoint should return file tree."""
        mock_get_service.return_value = mock_podcast_service

        response = client.get("/api/v1/repository/test1234/structure")

        assert response.status_code == 200
        data = response.json()
        assert data["repo_id"] == "test1234"
        assert "root" in data

    @patch("app.api.routes.repository.get_podcast_service")
    def test_get_repository_structure_not_found(self, mock_get_service, client):
        """Structure endpoint should return 404 for unknown repo."""
        mock_service = MagicMock()
        mock_service.get_file_tree = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/repository/unknown/structure")

        assert response.status_code == 404


class TestPodcastRoutes:
    """Tests for podcast endpoints."""

    @patch("app.api.routes.podcast.get_podcast_service")
    def test_create_podcast_success(self, mock_get_service, client, mock_podcast_service):
        """Create podcast endpoint should start generation."""
        mock_get_service.return_value = mock_podcast_service

        response = client.post(
            "/api/v1/podcast/create",
            json={
                "repo_id": "test1234",
                "selected_files": ["main.py", "src/utils.py"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["podcast_id"] == "pod1234"
        assert data["status"] == "pending"

    @patch("app.api.routes.podcast.get_podcast_service")
    def test_create_podcast_repo_not_found(self, mock_get_service, client):
        """Create podcast should return 400 if repo not found."""
        mock_service = MagicMock()
        mock_service.create_podcast = AsyncMock(
            side_effect=ValueError("Repository not found")
        )
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/podcast/create",
            json={"repo_id": "unknown", "selected_files": []},
        )

        assert response.status_code == 400

    @patch("app.api.routes.podcast.get_podcast_service")
    def test_get_podcast_status(self, mock_get_service, client, mock_podcast_service):
        """Status endpoint should return podcast status."""
        mock_get_service.return_value = mock_podcast_service

        response = client.get("/api/v1/podcast/pod1234/status")

        assert response.status_code == 200
        data = response.json()
        assert data["podcast_id"] == "pod1234"
        assert data["status"] == "completed"
        assert data["progress"] == 100.0

    @patch("app.api.routes.podcast.get_podcast_service")
    def test_get_podcast_status_not_found(self, mock_get_service, client):
        """Status endpoint should return 404 for unknown podcast."""
        mock_service = MagicMock()
        mock_service.get_status = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/podcast/unknown/status")

        assert response.status_code == 404

    @patch("app.api.routes.podcast.get_podcast_service")
    def test_get_podcast_chapters(self, mock_get_service, client, mock_podcast_service):
        """Chapters endpoint should return chapter list."""
        mock_get_service.return_value = mock_podcast_service

        response = client.get("/api/v1/podcast/pod1234/chapters")

        assert response.status_code == 200
        data = response.json()
        assert len(data["chapters"]) == 2
        assert data["chapters"][0]["title"] == "Intro"

    @patch("app.api.routes.podcast.get_podcast_service")
    def test_get_podcast_audio_not_ready(self, mock_get_service, client):
        """Audio endpoint should return 404 if not ready."""
        mock_service = MagicMock()
        mock_service.get_audio_path = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/podcast/pod1234/audio")

        assert response.status_code == 404


class TestErrorHandling:
    """Tests for error handling across routes."""

    @patch("app.api.routes.repository.get_podcast_service")
    def test_internal_server_error(self, mock_get_service, client):
        """Should return 500 on unexpected errors."""
        mock_service = MagicMock()
        mock_service.analyze_repository = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/repository/analyze",
            json={"url": "https://github.com/user/repo"},
        )

        assert response.status_code == 500

    def test_validation_error(self, client):
        """Should return 422 for validation errors."""
        response = client.post(
            "/api/v1/repository/analyze",
            json={},  # Missing required 'url' field
        )

        assert response.status_code == 422
