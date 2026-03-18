"""Test data factories using factory-boy patterns."""

from typing import Any


class FileNodeFactory:
    """Factory for generating FileNode-like structures."""

    @staticmethod
    def create(
        name: str = "test_file.py",
        path: str = "test_file.py",
        is_dir: bool = False,
        children: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Create a single file node."""
        return {
            "name": name,
            "path": path,
            "is_dir": is_dir,
            "children": children if is_dir else None,
        }

    @staticmethod
    def create_directory(
        name: str = "src",
        path: str = "src",
        children: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Create a directory node."""
        return FileNodeFactory.create(
            name=name,
            path=path,
            is_dir=True,
            children=children or [],
        )

    @staticmethod
    def create_tree(depth: int = 2, files_per_level: int = 3) -> dict[str, Any]:
        """Create a sample file tree structure."""
        if depth == 0:
            return FileNodeFactory.create()

        children = []
        for i in range(files_per_level):
            if i % 2 == 0 and depth > 1:
                # Create subdirectory
                children.append(
                    FileNodeFactory.create_directory(
                        name=f"dir_{i}",
                        path=f"dir_{i}",
                        children=[
                            FileNodeFactory.create(
                                name=f"file_{j}.py",
                                path=f"dir_{i}/file_{j}.py",
                            )
                            for j in range(files_per_level - 1)
                        ],
                    )
                )
            else:
                # Create file
                ext = [".py", ".ts", ".js", ".md", ".json"][i % 5]
                children.append(
                    FileNodeFactory.create(
                        name=f"file_{i}{ext}",
                        path=f"file_{i}{ext}",
                    )
                )

        return FileNodeFactory.create_directory(
            name="root",
            path=".",
            children=children,
        )


class PodcastDataFactory:
    """Factory for generating podcast-related test data."""

    @staticmethod
    def create_podcast_state(
        podcast_id: str = "abc12345",
        repo_id: str = "repo1234",
        status: str = "pending",
        progress: float = 0.0,
        selected_files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create podcast state data."""
        from datetime import datetime

        return {
            "repo_id": repo_id,
            "status": status,
            "progress": progress,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "selected_files": selected_files or ["main.py", "src/utils.py"],
            "title": f"Understanding Test Repo",
        }

    @staticmethod
    def create_chapter(
        chapter_id: int = 1,
        title: str = "Introduction",
        start_time: float = 0.0,
        end_time: float = 60.0,
    ) -> dict[str, Any]:
        """Create a chapter data structure."""
        return {
            "id": chapter_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
        }

    @staticmethod
    def create_chapters(count: int = 3) -> list[dict[str, Any]]:
        """Create multiple chapters with sequential times."""
        chapters = []
        current_time = 0.0
        titles = ["Introduction", "Main Content", "Advanced Topics", "Conclusion"]

        for i in range(count):
            duration = 60.0 + (i * 30)  # Variable durations
            chapters.append(
                PodcastDataFactory.create_chapter(
                    chapter_id=i + 1,
                    title=titles[i] if i < len(titles) else f"Chapter {i + 1}",
                    start_time=current_time,
                    end_time=current_time + duration,
                )
            )
            current_time += duration

        return chapters


class ScriptDataFactory:
    """Factory for generating script-related test data."""

    @staticmethod
    def create_section(
        chapter_id: int = 1,
        title: str = "Introduction",
        content: str = "This is the introduction content.",
        estimated_duration: float = 60.0,
    ) -> dict[str, Any]:
        """Create a script section."""
        return {
            "chapter_id": chapter_id,
            "title": title,
            "content": content,
            "estimated_duration": estimated_duration,
        }

    @staticmethod
    def create_raw_markdown(
        introduction: str = "Welcome to this podcast.",
        sections: list[tuple[str, str]] | None = None,
        conclusion: str = "Thank you for listening.",
    ) -> str:
        """Create raw markdown script content."""
        if sections is None:
            sections = [
                ("Main Module", "The main module contains core functionality."),
                ("Utilities", "Helper functions are defined here."),
            ]

        parts = [f"## Introduction\n\n{introduction}"]

        for title, content in sections:
            parts.append(f"## {title}\n\n{content}")

        parts.append(f"## Conclusion\n\n{conclusion}")

        return "\n\n".join(parts)
