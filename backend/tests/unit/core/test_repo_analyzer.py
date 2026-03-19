"""Unit tests for repository analyzer behavior."""

import tempfile
from pathlib import Path

import pytest

from app.core.repo_analyzer import RepoAnalyzer


@pytest.mark.asyncio
async def test_analyze_builds_local_structure_without_claude():
    analyzer = RepoAnalyzer.__new__(RepoAnalyzer)
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / "README.md").write_text("# Demo\n\nA demo project", encoding="utf-8")
        (repo / "app.py").write_text("print('hi')", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src" / "utils.py").write_text("def f():\n    return 1\n", encoding="utf-8")

        result = await analyzer.analyze(repo)

    assert result["name"] == repo.name
    assert result["file_count"] >= 2
    assert result["file_tree"]["is_dir"] is True


@pytest.mark.asyncio
async def test_analyze_handles_nonexistent_path():
    analyzer = RepoAnalyzer.__new__(RepoAnalyzer)
    repo_path = Path("/tmp/does-not-exist-podcast-anything")

    result = await analyzer.analyze(repo_path)
    assert result["name"] == repo_path.name
    assert result["file_count"] == 0
    assert result["file_tree"]["is_dir"] is False
