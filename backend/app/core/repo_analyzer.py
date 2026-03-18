"""Repository analysis module."""

import logging
import shutil
import time
from pathlib import Path

from git import Repo

from app.config import get_settings
from app.core.claude_client import ClaudeClient

settings = get_settings()
logger = logging.getLogger(__name__)


class RepoAnalyzer:
    """Analyzes GitHub repositories."""

    def __init__(self):
        self.claude_client = ClaudeClient()

    async def clone(self, url: str, repo_id: str) -> Path:
        """Clone a repository to a temporary directory."""
        # Create temp directory for this repo
        repo_path = Path(settings.temp_dir) / "repos" / repo_id
        repo_path.mkdir(parents=True, exist_ok=True)
        clone_start = time.monotonic()
        logger.info(
            "Cloning repository",
            extra={
                "repo_id": repo_id,
                "url": url,
                "repo_path": str(repo_path),
            },
        )

        # Clone the repository
        try:
            Repo.clone_from(url, repo_path, depth=1)
        except Exception as e:
            shutil.rmtree(repo_path, ignore_errors=True)
            logger.exception(
                "Repository clone failed",
                extra={
                    "repo_id": repo_id,
                    "url": url,
                    "repo_path": str(repo_path),
                },
            )
            raise ValueError(f"Failed to clone repository: {e}")

        logger.info(
            "Repository cloned",
            extra={
                "repo_id": repo_id,
                "url": url,
                "elapsed_seconds": round(time.monotonic() - clone_start, 2),
            },
        )
        return repo_path

    async def analyze(self, repo_path: Path) -> dict:
        """Analyze a cloned repository."""
        logger.info("Analyzing repository", extra={"repo_path": str(repo_path)})
        return await self.claude_client.get_file_structure(repo_path)

    def _manual_analysis(self, repo_path: Path) -> dict:
        """Manually analyze repository structure."""

        def build_tree(path: Path, base: Path) -> dict:
            relative = path.relative_to(base)
            node = {
                "name": path.name,
                "path": str(relative),
                "is_dir": path.is_dir(),
            }

            if path.is_dir():
                # Skip common non-source directories
                skip_dirs = {
                    ".git",
                    "node_modules",
                    "__pycache__",
                    ".venv",
                    "venv",
                    "build",
                    "dist",
                    ".idea",
                    ".vscode",
                }
                children = []
                for child in sorted(path.iterdir()):
                    if child.name in skip_dirs or child.name.startswith("."):
                        continue
                    children.append(build_tree(child, base))
                node["children"] = children

            return node

        # Count source files
        source_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
            ".rs", ".rb", ".php", ".c", ".cpp", ".h", ".cs",
            ".swift", ".kt", ".scala", ".clj", ".ex", ".erl",
        }
        file_count = sum(
            1
            for f in repo_path.rglob("*")
            if f.is_file() and f.suffix in source_extensions
        )

        # Try to get description from README
        description = ""
        for readme_name in ["README.md", "README.txt", "readme.md"]:
            readme_path = repo_path / readme_name
            if readme_path.exists():
                content = readme_path.read_text(encoding="utf-8", errors="ignore")
                # Get first paragraph
                lines = content.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        description = line[:200]
                        break
                break

        return {
            "name": repo_path.name,
            "description": description,
            "file_count": file_count,
            "file_tree": build_tree(repo_path, repo_path),
        }

    async def cleanup(self, repo_id: str):
        """Remove a cloned repository."""
        repo_path = Path(settings.temp_dir) / "repos" / repo_id
        if repo_path.exists():
            shutil.rmtree(repo_path, ignore_errors=True)
