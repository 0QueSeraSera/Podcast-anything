"""Repository-related test fixtures."""

from typing import Any


# Sample file tree for testing
SAMPLE_FILE_TREE: dict[str, Any] = {
    "name": "sample-project",
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
            "name": "pyproject.toml",
            "path": "pyproject.toml",
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
                    "name": "main.py",
                    "path": "src/main.py",
                    "is_dir": False,
                    "children": None,
                },
                {
                    "name": "utils.py",
                    "path": "src/utils.py",
                    "is_dir": False,
                    "children": None,
                },
                {
                    "name": "models",
                    "path": "src/models",
                    "is_dir": True,
                    "children": [
                        {
                            "name": "__init__.py",
                            "path": "src/models/__init__.py",
                            "is_dir": False,
                            "children": None,
                        },
                        {
                            "name": "user.py",
                            "path": "src/models/user.py",
                            "is_dir": False,
                            "children": None,
                        },
                    ],
                },
            ],
        },
        {
            "name": "tests",
            "path": "tests",
            "is_dir": True,
            "children": [
                {
                    "name": "__init__.py",
                    "path": "tests/__init__.py",
                    "is_dir": False,
                    "children": None,
                },
                {
                    "name": "test_main.py",
                    "path": "tests/test_main.py",
                    "is_dir": False,
                    "children": None,
                },
            ],
        },
    ],
}

# Sample repository analysis result
SAMPLE_REPO_ANALYSIS: dict[str, Any] = {
    "name": "sample-project",
    "description": "A sample project for testing",
    "file_count": 8,
    "file_tree": SAMPLE_FILE_TREE,
}

# Valid GitHub URLs for testing
VALID_GITHUB_URLS = [
    "https://github.com/user/repo",
    "https://github.com/user/repo.git",
    "https://github.com/organization/project-name",
    "http://github.com/user/repo",
    "https://github.com/user/repo-with-dashes",
    "https://github.com/user/repo.with.dots",
]

# Invalid URLs for testing
INVALID_URLS = [
    "not-a-url",
    "https://gitlab.com/user/repo",
    "https://bitbucket.org/user/repo",
    "ftp://github.com/user/repo",
    "github.com/user/repo",  # Missing protocol
    "",
]

# File extensions and their expected icons (for frontend testing)
FILE_EXTENSION_ICONS: dict[str, str] = {
    "py": "🐍",
    "js": "📜",
    "ts": "📘",
    "tsx": "⚛️",
    "jsx": "⚛️",
    "json": "📋",
    "md": "📝",
    "yaml": "⚙️",
    "yml": "⚙️",
    "html": "🌐",
    "css": "🎨",
    "go": "🐹",
    "rs": "🦀",
    "java": "☕",
    "rb": "💎",
    "php": "🐘",
}
