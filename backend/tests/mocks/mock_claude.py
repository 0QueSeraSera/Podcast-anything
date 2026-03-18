"""Mock for Claude CLI subprocess calls."""

import json
from typing import Any
from unittest.mock import MagicMock, patch


class MockClaudeResponse:
    """Mock response from Claude CLI."""

    def __init__(
        self,
        content: str = "Mocked Claude response",
        exit_code: int = 0,
        error: str | None = None,
    ):
        self.content = content
        self.exit_code = exit_code
        self.error = error

    @property
    def returncode(self) -> int:
        return self.exit_code

    @property
    def stdout(self) -> bytes:
        return self.content.encode()

    @property
    def stderr(self) -> bytes:
        return (self.error or "").encode()


class MockClaudeClient:
    """Mock ClaudeClient for testing without actual Claude CLI."""

    @staticmethod
    def get_sample_script(repo_name: str = "test-repo") -> str:
        """Generate a sample podcast script."""
        return f"""## Introduction

Welcome to this podcast about {repo_name}. We'll explore its architecture and key components.

## Core Architecture

The core architecture consists of several modules working together. The main entry point handles initialization.

## Key Components

The key components include utility functions, data models, and API endpoints. Each serves a specific purpose.

## Best Practices

This repository follows modern development practices including type hints, documentation, and testing.

## Conclusion

We've covered the main aspects of {repo_name}. It's a well-structured project worth studying.
"""

    @staticmethod
    def create_mock_subprocess(response: MockClaudeResponse | None = None):
        """Create a mock subprocess.run for Claude CLI calls."""
        if response is None:
            response = MockClaudeResponse(
                content=MockClaudeClient.get_sample_script()
            )

        mock_run = MagicMock(return_value=response)
        return mock_run


def mock_claude_client(module_path: str = "app.core.claude_client"):
    """Decorator/context manager to mock ClaudeClient."""
    sample_script = MockClaudeClient.get_sample_script()

    def decorator(func):
        async def wrapper(*args, **kwargs):
            with patch(f"{module_path}.ClaudeClient") as mock_client_class:
                mock_instance = MagicMock()
                mock_instance.generate_script = MagicMock(
                    return_value=sample_script
                )
                # Make it async
                import asyncio

                async def async_generate(*a, **kw):
                    return sample_script

                mock_instance.generate_script = async_generate
                mock_client_class.return_value = mock_instance

                return await func(*args, **kwargs)

        return wrapper

    return decorator


def patch_claude_subprocess(sample_script: str | None = None):
    """Patch subprocess calls to Claude CLI."""
    if sample_script is None:
        sample_script = MockClaudeClient.get_sample_script()

    response = MockClaudeResponse(content=sample_script)

    def decorator(func):
        import subprocess

        return patch("subprocess.run", return_value=response)(func)

    return decorator
