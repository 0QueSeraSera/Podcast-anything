"""Script generation module."""

import re
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.core.claude_client import ClaudeClient
from app.models.schemas import GeneratedScript, ScriptSection

settings = get_settings()


class ScriptGenerator:
    """Generates educational podcast scripts from repositories."""

    def __init__(self):
        self.claude_client = ClaudeClient()

    async def generate(
        self,
        repo_path: Path,
        repo_name: str,
        selected_files: list[str],
    ) -> GeneratedScript:
        """Generate a podcast script for the repository."""
        # Get raw script from Claude
        raw_script = await self.claude_client.generate_script(
            repo_path=repo_path,
            repo_name=repo_name,
            selected_files=selected_files,
        )

        # Parse into structured format
        return self._parse_script(raw_script, repo_name)

    def _parse_script(self, raw_script: str, repo_name: str) -> GeneratedScript:
        """Parse raw markdown script into structured format."""
        # Extract sections
        sections = []
        introduction = ""
        conclusion = ""

        # Split by ## headers
        parts = re.split(r"^##\s+", raw_script, flags=re.MULTILINE)

        chapter_id = 1
        for part in parts[1:]:  # Skip first empty part
            lines = part.strip().split("\n")
            if not lines:
                continue

            title = lines[0].strip()
            content = "\n".join(lines[1:]).strip()

            # Categorize by title
            title_lower = title.lower()
            if "introduction" in title_lower or "intro" in title_lower:
                introduction = content
            elif "conclusion" in title_lower or "summary" in title_lower:
                conclusion = content
            else:
                # Estimate duration (~150 words per minute)
                word_count = len(content.split())
                estimated_duration = (word_count / 150) * 60

                sections.append(
                    ScriptSection(
                        chapter_id=chapter_id,
                        title=title,
                        content=content,
                        estimated_duration=estimated_duration,
                    )
                )
                chapter_id += 1

        # Calculate total duration
        total_duration = sum(s.estimated_duration for s in sections)
        # Add intro/conclusion
        total_duration += (len(introduction.split()) / 150) * 60
        total_duration += (len(conclusion.split()) / 150) * 60

        return GeneratedScript(
            repo_name=repo_name,
            title=f"Understanding {repo_name}",
            introduction=introduction,
            sections=sections,
            conclusion=conclusion,
            total_estimated_duration=total_duration,
        )
