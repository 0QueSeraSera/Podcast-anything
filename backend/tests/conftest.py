"""Shared pytest fixtures for backend tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        anthropic_api_key="test-anthropic-key",
        dashscope_api_key="test-dashscope-key",
        app_name="TestApp",
        app_version="0.0.0-test",
        debug=True,
        temp_dir="/tmp/test-podcast-anything",
        audio_output_dir="/tmp/test-podcast-anything/audio",
        tts_model="test-tts-model",
        tts_voice="test-voice",
        tts_chunk_size=500,
        redis_url="redis://localhost:6379/1",
    )


@pytest.fixture
def sample_repo_path(tmp_path: Path) -> Path:
    """Create a temporary directory with sample repository files."""
    repo_dir = tmp_path / "sample-repo"
    repo_dir.mkdir()

    # Create sample files
    (repo_dir / "README.md").write_text("# Sample Repo\n\nThis is a sample repository.")
    (repo_dir / "main.py").write_text('print("Hello, World!")')

    src_dir = repo_dir / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "utils.py").write_text("def helper():\n    return 42")

    return repo_dir


@pytest.fixture
def sample_script() -> str:
    """Sample markdown script content."""
    return """## Introduction

Welcome to this podcast about the sample repository. We'll explore its structure and functionality.

## Main Module

The main module contains the entry point for the application. It prints a greeting message.

## Utility Functions

The utils module provides helper functions. The helper function returns the answer to everything.

## Conclusion

We've covered the main components of this repository. It's a simple but well-structured project.
"""


@pytest.fixture
def sample_file_tree() -> dict:
    """Sample file tree structure."""
    return {
        "name": "sample-repo",
        "path": ".",
        "is_dir": True,
        "children": [
            {
                "name": "README.md",
                "path": "README.md",
                "is_dir": False,
                "children": None,
            },
            {
                "name": "main.py",
                "path": "main.py",
                "is_dir": False,
                "children": None,
            },
            {
                "name": "src",
                "path": "src",
                "is_dir": True,
                "children": [
                    {
                        "name": "__init__.py",
                        "path": "src/__init__.py",
                        "is_dir": False,
                        "children": None,
                    },
                    {
                        "name": "utils.py",
                        "path": "src/utils.py",
                        "is_dir": False,
                        "children": None,
                    },
                ],
            },
        ],
    }


@pytest.fixture
def clean_singleton():
    """Reset PodcastService singleton between tests."""
    from app.services import podcast_service

    # Reset before test
    podcast_service._podcast_service_instance = None

    yield

    # Reset after test
    podcast_service._podcast_service_instance = None


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch):
    """Set required environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")


@pytest.fixture
def mock_settings_cache():
    """Clear the settings cache to allow fresh settings."""
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
