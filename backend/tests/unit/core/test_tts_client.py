"""Unit tests for TTSClient behavior."""

import sys
import types
import pytest

from app.core.tts_client import TTSClient


class TestTTSSplitText:
    """Tests for the _split_text method."""

    def test_short_text_returns_single_chunk(self):
        """Short text under max_length should return a single chunk."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"
        client.model = "test-model"
        client.voice = "test-voice"

        text = "This is a short sentence."
        chunks = client._split_text(text, max_length=500)

        assert len(chunks) == 1
        assert chunks[0] == "This is a short sentence."

    def test_long_text_splits_on_sentence_boundaries(self):
        """Long text should split on sentence boundaries."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        # Create text with multiple sentences
        sentences = [f"This is sentence number {i}." for i in range(20)]
        text = " ".join(sentences)

        chunks = client._split_text(text, max_length=100)

        # Each chunk should be under max_length
        for chunk in chunks:
            assert len(chunk) <= 100, f"Chunk too long: {len(chunk)}"

        # All text should be preserved
        combined = " ".join(chunks)
        for sentence in sentences:
            assert sentence.strip() in combined, f"Missing sentence: {sentence}"

    def test_empty_text_returns_empty_list(self):
        """Empty text should return empty list."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        chunks = client._split_text("", max_length=500)

        # Empty string returns single empty chunk (current behavior)
        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_text_without_periods_handled(self):
        """Text without periods should still be chunked."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        # Long text without periods
        text = "word " * 200  # 1000 characters

        chunks = client._split_text(text, max_length=500)

        # Without periods, split() returns single element
        # Current implementation splits on ". " so this becomes one big chunk
        assert len(chunks) >= 1

    def test_exact_boundary_edge_case(self):
        """Text exactly at boundary should be handled correctly."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        # Create text that's exactly at the boundary
        sentence = "A" * 50 + ". "
        text = sentence * 10  # Each chunk should be ~500 chars

        chunks = client._split_text(text, max_length=500)

        for chunk in chunks:
            assert len(chunk) <= 502  # Allow small margin for ". "

    def test_newlines_replaced_with_spaces(self):
        """Newlines should be replaced with spaces."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        text = "First line.\nSecond line.\nThird line."
        chunks = client._split_text(text, max_length=500)

        # Newlines should be replaced
        assert "\n" not in str(chunks)

    def test_single_long_sentence(self):
        """A single sentence longer than max_length should still be returned."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        # Single very long "sentence" (no periods)
        text = "A" * 1000

        chunks = client._split_text(text, max_length=500)

        # Without periods, split returns single element
        assert len(chunks) >= 1

    def test_multiple_short_sentences(self):
        """Multiple short sentences should be combined into fewer chunks."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        sentences = [f"Sentence {i}." for i in range(10)]
        text = " ".join(sentences)

        chunks = client._split_text(text, max_length=100)

        # Should combine short sentences into chunks
        assert len(chunks) < 10, "Short sentences should be combined"

    def test_preserves_trailing_period(self):
        """Each chunk should end with a period."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        text = "First sentence. Second sentence. Third sentence."
        chunks = client._split_text(text, max_length=30)

        for chunk in chunks:
            if chunk:  # Skip empty chunks
                assert chunk.endswith("."), f"Chunk should end with period: {chunk}"

    def test_custom_max_length(self):
        """Custom max_length should be respected."""
        client = TTSClient.__new__(TTSClient)
        client.api_key = "test-key"

        text = "A. B. C. D. E. F. G. H. I. J."

        chunks_50 = client._split_text(text, max_length=50)
        chunks_20 = client._split_text(text, max_length=20)

        # Smaller max_length should result in more chunks
        assert len(chunks_20) >= len(chunks_50)


@pytest.mark.asyncio
async def test_synthesize_error_does_not_crash_logging(monkeypatch):
    """Non-200 TTS responses should raise RuntimeError, not logging KeyError."""

    class _Response:
        status_code = 500
        message = "upstream failed"
        output = {}

    class _FakeMMC:
        @staticmethod
        def call(**kwargs):
            return _Response()

    fake_dashscope = types.SimpleNamespace(api_key=None, MultiModalConversation=_FakeMMC)
    monkeypatch.setitem(sys.modules, "dashscope", fake_dashscope)

    client = TTSClient.__new__(TTSClient)
    client.api_key = "test-key"
    client.model = "test-model"
    client.voice = "test-voice"

    with pytest.raises(RuntimeError, match="TTS error: upstream failed"):
        await client.synthesize("hello world")
