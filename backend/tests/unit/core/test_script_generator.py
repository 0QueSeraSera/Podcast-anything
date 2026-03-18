"""Unit tests for ScriptGenerator._parse_script() method."""

import pytest

from app.core.script_generator import ScriptGenerator
from app.models.schemas import GeneratedScript, ScriptSection


class TestScriptGeneratorParseScript:
    """Tests for the _parse_script method."""

    @pytest.fixture
    def generator(self):
        """Create a ScriptGenerator instance (without Claude client)."""
        gen = ScriptGenerator.__new__(ScriptGenerator)
        gen.claude_client = None
        return gen

    def test_parse_markdown_with_headers(self, generator):
        """Parse markdown with ## headers."""
        raw_script = """## Introduction

Welcome to the podcast.

## Main Content

This is the main content.

## Conclusion

Thank you for listening.
"""
        result = generator._parse_script(raw_script, "test-repo")

        assert result.repo_name == "test-repo"
        assert result.title == "Understanding test-repo"
        assert result.introduction == "Welcome to the podcast."
        assert result.conclusion == "Thank you for listening."
        assert len(result.sections) == 1
        assert result.sections[0].title == "Main Content"

    def test_extract_introduction(self, generator):
        """Extract introduction section."""
        raw_script = """## Introduction

This is the intro content.

## Section One

Content here.
"""
        result = generator._parse_script(raw_script, "test-repo")

        assert result.introduction == "This is the intro content."

    def test_extract_conclusion(self, generator):
        """Extract conclusion section."""
        raw_script = """## Section One

Content here.

## Conclusion

This is the conclusion.
"""
        result = generator._parse_script(raw_script, "test-repo")

        assert result.conclusion == "This is the conclusion."

    def test_extract_summary_as_conclusion(self, generator):
        """Extract summary section as conclusion."""
        raw_script = """## Section One

Content here.

## Summary

This is the summary.
"""
        result = generator._parse_script(raw_script, "test-repo")

        assert result.conclusion == "This is the summary."

    def test_parse_multiple_chapters(self, generator):
        """Parse multiple chapter sections."""
        raw_script = """## Introduction

Intro.

## Chapter One

First chapter content.

## Chapter Two

Second chapter content.

## Conclusion

End.
"""
        result = generator._parse_script(raw_script, "test-repo")

        assert len(result.sections) == 2
        assert result.sections[0].title == "Chapter One"
        assert result.sections[1].title == "Chapter Two"

    def test_duration_estimation_from_word_count(self, generator):
        """Estimate duration based on word count (~150 words per minute)."""
        # Create content with known word count
        content = "word " * 300  # 300 words = 2 minutes = 120 seconds
        raw_script = f"""## Introduction

Intro.

## Chapter

{content}

## Conclusion

End.
"""
        result = generator._parse_script(raw_script, "test-repo")

        # 300 words at 150 wpm = 2 minutes = 120 seconds
        expected_duration = (300 / 150) * 60  # 120 seconds
        assert abs(result.sections[0].estimated_duration - expected_duration) < 1

    def test_total_duration_calculation(self, generator):
        """Calculate total duration including intro and conclusion."""
        intro = "word " * 150  # 60 seconds
        content = "word " * 150  # 60 seconds
        conclusion = "word " * 75  # 30 seconds

        raw_script = f"""## Introduction

{intro}

## Chapter

{content}

## Conclusion

{conclusion}
"""
        result = generator._parse_script(raw_script, "test-repo")

        # Total: 60 + 60 + 30 = 150 seconds
        assert result.total_estimated_duration >= 140  # Allow some margin
        assert result.total_estimated_duration <= 160

    def test_handle_malformed_input(self, generator):
        """Handle malformed or incomplete input."""
        raw_script = "This has no headers at all."
        result = generator._parse_script(raw_script, "test-repo")

        # Should still return a valid result
        assert result.repo_name == "test-repo"
        assert result.introduction == ""
        assert result.conclusion == ""
        assert len(result.sections) == 0

    def test_empty_script(self, generator):
        """Handle empty script."""
        result = generator._parse_script("", "test-repo")

        assert result.repo_name == "test-repo"
        assert result.introduction == ""
        assert result.conclusion == ""

    def test_chapter_id_sequential(self, generator):
        """Chapter IDs should be sequential."""
        raw_script = """## Chapter A

Content A.

## Chapter B

Content B.

## Chapter C

Content C.
"""
        result = generator._parse_script(raw_script, "test-repo")

        for i, section in enumerate(result.sections):
            assert section.chapter_id == i + 1

    def test_intro_variant_detection(self, generator):
        """Detect 'intro' as introduction."""
        raw_script = """## Intro

This is the intro.

## Main

Content.
"""
        result = generator._parse_script(raw_script, "test-repo")

        assert result.introduction == "This is the intro."

    def test_multiline_content(self, generator):
        """Handle multiline content in sections."""
        raw_script = """## Chapter

Line one.
Line two.
Line three.

## Conclusion

Done.
"""
        result = generator._parse_script(raw_script, "test-repo")

        assert "Line one." in result.sections[0].content
        assert "Line two." in result.sections[0].content
        assert "Line three." in result.sections[0].content

    def test_returns_generated_script_model(self, generator):
        """Should return a GeneratedScript model."""
        raw_script = """## Introduction

Intro.

## Chapter

Content.

## Conclusion

End.
"""
        result = generator._parse_script(raw_script, "test-repo")

        assert isinstance(result, GeneratedScript)
        assert isinstance(result.sections[0], ScriptSection)
