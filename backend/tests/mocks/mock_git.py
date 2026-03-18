"""Mock for Git operations using GitPython."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch


class MockGitRepo:
    """Mock GitPython Repo object."""

    def __init__(
        self,
        path: Path,
        name: str = "mock-repo",
        description: str = "A mock repository",
    ):
        self.path = path
        self._name = name
        self._description = description
        self.active_branch = MagicMock()
        self.active_branch.name = "main"

    @property
    def working_dir(self) -> str:
        return str(self.path)

    @property
    def description(self) -> str:
        return self._description

    def __str__(self):
        return f"MockGitRepo({self._name})"


class MockRepoAnalyzer:
    """Mock RepoAnalyzer for testing without actual git operations."""

    def __init__(self, repo_path: Path | None = None):
        self.repo_path = repo_path

    async def clone(self, url: str, repo_id: str) -> Path:
        """Mock clone operation - creates a temp directory with sample files."""
        # Create a temporary directory structure
        repo_dir = Path(tempfile.mkdtemp(prefix=f"mock_repo_{repo_id}_"))

        # Extract repo name from URL
        repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")

        # Create sample files
        (repo_dir / "README.md").write_text(f"# {repo_name}\n\nSample repository for testing.")
        (repo_dir / "main.py").write_text('print("Hello from mock repo")')

        src_dir = repo_dir / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")
        (src_dir / "main.py").write_text("def main():\n    pass")

        self.repo_path = repo_dir
        return repo_dir

    async def analyze(self, repo_path: Path) -> dict[str, Any]:
        """Mock analyze operation."""
        # Count files
        file_count = sum(1 for _ in repo_path.rglob("*") if _.is_file())

        # Build file tree
        file_tree = self._build_file_tree(repo_path, repo_path)

        return {
            "name": repo_path.name,
            "description": "Mock repository for testing",
            "file_count": file_count,
            "file_tree": file_tree,
        }

    def _build_file_tree(self, base_path: Path, current_path: Path) -> dict[str, Any]:
        """Build a file tree structure."""
        relative_path = current_path.relative_to(base_path)
        path_str = str(relative_path) if str(relative_path) != "." else "."

        node = {
            "name": current_path.name,
            "path": path_str,
            "is_dir": current_path.is_dir(),
            "children": None,
        }

        if current_path.is_dir():
            children = []
            for child in sorted(current_path.iterdir()):
                if child.name.startswith("."):
                    continue
                children.append(self._build_file_tree(base_path, child))
            node["children"] = children

        return node


def patch_git_clone():
    """Patch GitPython clone operations."""
    mock_repo_class = MagicMock()

    def create_mock_repo(clone_url: str, to_path: str | Path | None = None, **kwargs):
        """Create a mock repo when clone is called."""
        if to_path is None:
            to_path = Path(tempfile.mkdtemp(prefix="mock_git_clone_"))
        elif isinstance(to_path, str):
            to_path = Path(to_path)

        to_path.mkdir(parents=True, exist_ok=True)

        # Create sample files
        repo_name = clone_url.rstrip("/").split("/")[-1].replace(".git", "")
        (to_path / "README.md").write_text(f"# {repo_name}")
        (to_path / "main.py").write_text("# Main file")

        return MockGitRepo(to_path, name=repo_name)

    mock_repo_class.clone_from = MagicMock(side_effect=create_mock_repo)

    return patch("git.Repo", mock_repo_class)


def create_sample_repo_at_path(path: Path, name: str = "sample-repo") -> dict[str, Any]:
    """Create a sample repository structure at the given path."""
    path.mkdir(parents=True, exist_ok=True)

    files = {
        "README.md": f"# {name}\n\nSample repository.",
        "pyproject.toml": "[project]\nname = 'sample'",
        "main.py": "def main():\n    pass",
    }

    dirs = {
        "src": {
            "__init__.py": "",
            "utils.py": "def helper():\n    return 42",
            "main.py": "from .utils import helper",
        },
        "tests": {
            "__init__.py": "",
            "test_main.py": "def test_main():\n    pass",
        },
    }

    # Create files
    for filename, content in files.items():
        (path / filename).write_text(content)

    # Create directories with files
    for dirname, dir_files in dirs.items():
        dir_path = path / dirname
        dir_path.mkdir()
        for filename, content in dir_files.items():
            (dir_path / filename).write_text(content)

    return {
        "name": name,
        "path": str(path),
        "file_count": sum(1 for _ in path.rglob("*") if _.is_file()),
    }
