"""Unit tests for Claude client subprocess behavior."""

from pathlib import Path

import pytest

from app.core.claude_client import ClaudeClient


class _FakeProcess:
    def __init__(self, returncode: int = 0, stdout: bytes = b"{}", stderr: bytes = b""):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self):
        return self._stdout, self._stderr


@pytest.mark.asyncio
async def test_analyze_codebase_preserves_path(monkeypatch):
    """Subprocess should run from repo path without overriding environment."""
    captured = {}

    async def fake_create_subprocess_exec(*cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _FakeProcess()

    monkeypatch.setattr("app.core.claude_client.asyncio.create_subprocess_exec", fake_create_subprocess_exec)

    client = ClaudeClient()
    result = await client.analyze_codebase(Path("."), "test prompt")

    assert result == "{}"
    assert captured["cmd"][0] == "claude"
    assert "--cwd" not in captured["cmd"]
    assert captured["kwargs"]["cwd"] == "."
    assert "env" not in captured["kwargs"]


@pytest.mark.asyncio
async def test_analyze_codebase_missing_claude_has_clear_error(monkeypatch):
    """Missing claude binary should raise a clear RuntimeError."""

    async def fake_create_subprocess_exec(*cmd, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", "claude")

    monkeypatch.setattr("app.core.claude_client.asyncio.create_subprocess_exec", fake_create_subprocess_exec)

    client = ClaudeClient()
    with pytest.raises(RuntimeError, match="Claude CLI"):
        await client.analyze_codebase(Path("."), "test prompt")
