"""Unit tests for repository analyzer behavior."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.repo_analyzer import RepoAnalyzer


@pytest.mark.asyncio
async def test_analyze_uses_claude_client_result():
    analyzer = RepoAnalyzer.__new__(RepoAnalyzer)
    analyzer.claude_client = MagicMock()
    analyzer.claude_client.get_file_structure = AsyncMock(
        return_value={"name": "repo", "file_count": 1, "file_tree": {"name": "repo", "is_dir": True, "path": ""}}
    )

    result = await analyzer.analyze(Path("."))

    assert result["name"] == "repo"
    analyzer.claude_client.get_file_structure.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_propagates_claude_errors():
    analyzer = RepoAnalyzer.__new__(RepoAnalyzer)
    analyzer.claude_client = MagicMock()
    analyzer.claude_client.get_file_structure = AsyncMock(side_effect=RuntimeError("Claude CLI not found"))

    with pytest.raises(RuntimeError, match="Claude CLI not found"):
        await analyzer.analyze(Path("."))
