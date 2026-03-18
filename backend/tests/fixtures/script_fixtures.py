"""Script-related test fixtures."""

from typing import Any


# Sample raw script content with various sections
SAMPLE_RAW_SCRIPT = """## Introduction

Welcome to this educational podcast about the sample repository. Today we'll explore the architecture, key components, and design patterns used in this project.

## Main Module

The main module serves as the entry point for the application. It handles command-line arguments and orchestrates the initialization of other components. The code is well-documented and follows Python best practices.

## Core Components

The core components include the configuration manager, the service layer, and the data models. Each component is designed with separation of concerns in mind, making the codebase maintainable and testable.

## Utility Functions

Utility functions provide common operations used throughout the application. These include string manipulation, file operations, and validation helpers. They are pure functions with no side effects.

## Conclusion

We've covered the main aspects of this repository. The clean architecture and modular design make it an excellent reference for building similar projects.
"""

# Script with malformed sections
MALFORMED_SCRIPT = """
This is some text without proper headers.

##Introduction

Missing space after hash.

##

Empty title

## Valid Section

This section is valid.
"""

# Very long script for testing chunking
LONG_SCRIPT = """## Introduction

""" + "This is a sentence. " * 100 + """

## Main Content

""" + "More content here. " * 200 + """

## Conclusion

""" + "Final words. " * 50


def get_sample_script_with_sections(section_count: int = 3) -> str:
    """Generate a sample script with a specific number of sections."""
    sections = [
        "## Introduction\n\nWelcome to this podcast.",
    ]

    for i in range(section_count):
        sections.append(
            f"## Section {i + 1}\n\nThis is the content for section {i + 1}. "
            f"It contains multiple sentences. Each sentence adds to the narrative."
        )

    sections.append("## Conclusion\n\nThank you for listening.")

    return "\n\n".join(sections)


def get_expected_sections() -> list[dict[str, Any]]:
    """Get expected parsed sections from SAMPLE_RAW_SCRIPT."""
    return [
        {
            "title": "Main Module",
            "word_count": 36,
        },
        {
            "title": "Core Components",
            "word_count": 30,
        },
        {
            "title": "Utility Functions",
            "word_count": 32,
        },
    ]
