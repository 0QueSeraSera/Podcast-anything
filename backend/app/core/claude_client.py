"""Claude Code SDK integration for repository analysis."""

import asyncio
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for interacting with Claude Code CLI."""

    def __init__(self):
        """Initialize Claude CLI client."""

    async def analyze_codebase(
        self,
        repo_path: Path,
        prompt: str,
    ) -> str:
        """
        Analyze a codebase using Claude Code CLI.

        Uses subprocess to invoke claude CLI with the repository as context.
        """
        # For MVP, we'll use subprocess to call the claude CLI
        # In production, use the claude-agent-sdk when available
        cmd = [
            "claude",
            "--print",
        ]
        start_time = time.monotonic()
        logger.info(
            "Starting Claude CLI analysis",
            extra={
                "repo_path": str(repo_path),
                "prompt_chars": len(prompt),
                "command": " ".join(cmd),
            },
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(repo_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as e:
            if e.filename == "claude":
                logger.exception("Claude CLI executable not found in PATH")
                raise RuntimeError(
                    "Claude CLI ('claude') was not found in PATH. Install it and ensure it is available to the backend process."
                ) from e
            raise

        stdout, stderr = await process.communicate(prompt.encode("utf-8"))
        elapsed = time.monotonic() - start_time

        if process.returncode != 0:
            logger.error(
                "Claude CLI exited with error",
                extra={
                    "repo_path": str(repo_path),
                    "return_code": process.returncode,
                    "elapsed_seconds": round(elapsed, 2),
                    "stderr_preview": stderr.decode("utf-8", errors="ignore")[:500],
                },
            )
            raise RuntimeError(f"Claude CLI error: {stderr.decode()}")

        logger.info(
            "Claude CLI analysis completed",
            extra={
                "repo_path": str(repo_path),
                "elapsed_seconds": round(elapsed, 2),
                "stdout_chars": len(stdout),
            },
        )
        return stdout.decode()

    async def get_file_structure(self, repo_path: Path) -> dict:
        """Get the file structure of a repository."""
        prompt = """Analyze this repository and return a JSON object with the following structure:
{
  "name": "repository name",
  "description": "brief description",
  "file_count": number of files,
  "file_tree": {
    "name": "root",
    "path": "",
    "is_dir": true,
    "children": [... recursive structure ...]
  }
}

Focus on source code files (.py, .js, .ts, .java, etc.) and configuration files.
Exclude node_modules, .git, __pycache__, and other common directories.
Return ONLY the JSON object, no other text."""

        result = await self.analyze_codebase(repo_path, prompt)

        # Extract JSON from response
        try:
            # Try to find JSON in the response
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(result[start:end])
            return json.loads(result)
        except json.JSONDecodeError:
            # Fallback: build structure manually
            return self._build_file_tree(repo_path)

    def _build_file_tree(self, repo_path: Path) -> dict:
        """Build file tree manually as fallback."""

        def build_node(path: Path, base_path: Path) -> dict:
            relative = path.relative_to(base_path)
            node = {
                "name": path.name,
                "path": str(relative),
                "is_dir": path.is_dir(),
            }
            if path.is_dir():
                children = []
                for child in sorted(path.iterdir()):
                    if child.name.startswith(".") or child.name in [
                        "node_modules",
                        "__pycache__",
                        "venv",
                        ".venv",
                    ]:
                        continue
                    children.append(build_node(child, base_path))
                node["children"] = children
            return node

        return {
            "name": repo_path.name,
            "description": "",
            "file_count": sum(1 for _ in repo_path.rglob("*") if _.is_file()),
            "file_tree": build_node(repo_path, repo_path),
        }

    async def generate_script(
        self,
        repo_path: Path,
        repo_name: str,
        selected_files: list[str],
    ) -> str:
        """Generate an educational podcast script for the repository."""
        files_context = "\n".join(f"- {f}" for f in selected_files) if selected_files else "all files"

        prompt = f"""Create an educational podcast script explaining this codebase: {repo_name}

Focus on these files/directories:
{files_context}

Generate a script with the following structure:

# Introduction
[Brief overview of what this project does and who it's for]

# Chapter 1: Architecture Overview
[Explain the high-level architecture and main components]

# Chapter 2-N: Key Components
[For each major component, explain its purpose and how it works]

# Conclusion
[Summary and key takeaways]

Guidelines:
- Write in a conversational, educational tone
- Explain concepts as if teaching a developer who is new to the codebase
- Include specific code examples where helpful
- Each chapter should be 2-3 minutes when read aloud
- Use clear section headers with ## for chapters

Return the complete script as markdown."""

        return await self.analyze_codebase(repo_path, prompt)
