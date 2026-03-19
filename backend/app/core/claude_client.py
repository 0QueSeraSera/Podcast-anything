"""Claude Code SDK integration for repository analysis."""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ClaudeClient:
    """Client for interacting with Claude Code CLI."""

    def __init__(self):
        """Initialize Claude CLI client."""
        self.last_output_path: Path | None = None

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

        output_text = stdout.decode()
        logger.info(
            "Claude CLI analysis completed",
            extra={
                "repo_path": str(repo_path),
                "elapsed_seconds": round(elapsed, 2),
                "stdout_chars": len(output_text),
            },
        )
        logger.info(
            "Claude CLI output captured",
            extra={
                "repo_path": str(repo_path),
                "output_preview": re.sub(r"\s+", " ", output_text).strip()[:400],
            },
        )
        preview = re.sub(r"\s+", " ", output_text).strip()[:400]
        logger.info("Claude CLI output preview: %s", preview)
        output_path = self._persist_cli_output(repo_path=repo_path, output_text=output_text)
        self.last_output_path = output_path
        if output_path:
            logger.info(
                "Claude CLI output persisted",
                extra={
                    "repo_path": str(repo_path),
                    "output_path": str(output_path),
                    "output_bytes": output_path.stat().st_size,
                },
            )
        return output_text

    def _persist_cli_output(self, repo_path: Path, output_text: str) -> Path | None:
        """Persist raw Claude CLI output for debugging and inspection."""
        try:
            output_dir = Path(settings.claude_output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            safe_repo = re.sub(r"[^a-zA-Z0-9._-]+", "-", repo_path.name).strip("-") or "repo"
            file_path = output_dir / f"{timestamp}-{safe_repo}-script.md"
            file_path.write_text(output_text, encoding="utf-8")
            return file_path
        except Exception:
            logger.exception(
                "Failed to persist Claude CLI output",
                extra={"repo_path": str(repo_path)},
            )
            return None

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
        learning_preferences: str | None = None,
    ) -> str:
        """Generate an educational podcast script for the repository."""
        files_context = "\n".join(f"- {f}" for f in selected_files) if selected_files else "all files"
        preferences = (learning_preferences or "").strip()
        preferences_block = ""
        if preferences:
            preferences_block = f"""

Learner scope preferences:
{preferences}

Use these preferences to prioritize topics the learner wants and avoid topics they do not want."""

        prompt = f"""Create an educational podcast script explaining this codebase: {repo_name}

Focus on these files/directories:
{files_context}
{preferences_block}

You MUST return plain markdown in this exact high-level structure:
## Introduction
[2-4 short paragraphs introducing what the project does, who it is for, and how to think about it]

## Architecture Overview
[Explain the high-level architecture and main components]

## [Key Component 1]
[How it works and why it matters]

## [Key Component 2]
[How it works and why it matters]

## Conclusion
[Concise summary and key takeaways]

Formatting constraints (strict):
- Use only level-2 headers (`##`) for all sections.
- Do NOT use level-1 headers (`#`), code fences, tables, HTML, or block quotes.
- Do NOT include raw JSON, XML, stack traces, shell transcripts, or long symbol-heavy snippets.
- Keep sentences natural for text-to-speech; avoid uncommon Unicode symbols.
- If referencing code, describe it in prose rather than pasting large code blocks.

Content guidelines:
- Write in a conversational, educational tone for developers new to the codebase.
- Each non-introduction/non-conclusion section should target about 2-3 minutes when read aloud.
- Prefer short paragraphs and smooth transitions between sections.

Return only the final markdown script, with no preamble or postscript."""

        return await self.analyze_codebase(repo_path, prompt)
