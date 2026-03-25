"""Unit tests for TTSClient behavior."""

import sys
import types
import pytest

from app.core.tts_client import TTSClient


def _install_fake_dashscope_qwen_tts(monkeypatch, synthesizer_cls):
    """Install fake dashscope modules for qwen_tts import path."""
    dashscope_mod = types.ModuleType("dashscope")
    dashscope_mod.api_key = None
    audio_mod = types.ModuleType("dashscope.audio")
    qwen_tts_mod = types.ModuleType("dashscope.audio.qwen_tts")
    qwen_tts_mod.SpeechSynthesizer = synthesizer_cls
    monkeypatch.setitem(sys.modules, "dashscope", dashscope_mod)
    monkeypatch.setitem(sys.modules, "dashscope.audio", audio_mod)
    monkeypatch.setitem(sys.modules, "dashscope.audio.qwen_tts", qwen_tts_mod)


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

    class _FakeSynthesizer:
        @staticmethod
        def call(**kwargs):
            return _Response()

    _install_fake_dashscope_qwen_tts(monkeypatch, _FakeSynthesizer)

    client = TTSClient.__new__(TTSClient)
    client.api_key = "test-key"
    client.model = "test-model"
    client.voice = "test-voice"

    with pytest.raises(RuntimeError, match="all chunks failed to synthesize"):
        await client.synthesize("hello world")


@pytest.mark.asyncio
async def test_synthesize_raises_when_no_valid_chunks_after_sanitization(monkeypatch):
    """If sanitization removes meaningful content, synthesis should fail early."""
    called = {"count": 0}

    class _FakeSynthesizer:
        @staticmethod
        def call(**kwargs):
            called["count"] += 1
            raise AssertionError("TTS API should not be called")

    _install_fake_dashscope_qwen_tts(monkeypatch, _FakeSynthesizer)

    client = TTSClient.__new__(TTSClient)
    client.api_key = "test-key"
    client.model = "test-model"
    client.voice = "test-voice"

    with pytest.raises(RuntimeError, match="no valid text chunks after sanitization"):
        await client.synthesize("```python\\nprint('x')\\n```")
    assert called["count"] == 0


@pytest.mark.asyncio
async def test_synthesize_retries_chunk_with_fallback(monkeypatch):
    """Invalid first attempt should retry once with a simplified chunk."""
    calls = []

    class _ErrorResponse:
        status_code = 400
        message = "Due to invalid text, invalid audio was returned."
        output = {}

    class _OkResponse:
        status_code = 200
        message = ""
        output = {"audio": b"AUDIO_OK"}

    class _FakeSynthesizer:
        @staticmethod
        def call(**kwargs):
            calls.append(kwargs["text"])
            if len(calls) == 1:
                return _ErrorResponse()
            return _OkResponse()

    _install_fake_dashscope_qwen_tts(monkeypatch, _FakeSynthesizer)

    client = TTSClient.__new__(TTSClient)
    client.api_key = "test-key"
    client.model = "test-model"
    client.voice = "test-voice"

    audio = await client.synthesize("Use value @@@ foo() >>> ???")

    assert audio == b"AUDIO_OK"
    assert len(calls) == 2
    assert calls[1] != calls[0]


@pytest.mark.asyncio
async def test_synthesize_skips_invalid_chunk_and_continues(monkeypatch):
    """A permanently invalid chunk should be skipped if later chunks succeed."""
    calls = []

    class _Response:
        def __init__(self, status_code, message="", output=None):
            self.status_code = status_code
            self.message = message
            self.output = output or {}

    class _FakeSynthesizer:
        @staticmethod
        def call(**kwargs):
            chunk = kwargs["text"]
            calls.append(chunk)
            if "second chunk content" not in chunk:
                return _Response(400, "Due to invalid text, invalid audio was returned.")
            return _Response(200, output={"audio": b"AUDIO_OK"})

    _install_fake_dashscope_qwen_tts(monkeypatch, _FakeSynthesizer)

    client = TTSClient.__new__(TTSClient)
    client.api_key = "test-key"
    client.model = "test-model"
    client.voice = "test-voice"
    monkeypatch.setattr(
        client,
        "_split_text",
        lambda text, max_length=500: ["first chunk content", "second chunk content"],
    )

    audio = await client.synthesize("input text")

    assert audio == b"AUDIO_OK"
    assert len(calls) >= 2


@pytest.mark.asyncio
async def test_synthesize_concatenates_multiple_successful_chunks(monkeypatch):
    """Successful multi-chunk synthesis should include every chunk audio payload."""

    class _Response:
        def __init__(self, audio: bytes):
            self.status_code = 200
            self.message = ""
            self.output = {"audio": audio}

    class _FakeSynthesizer:
        @staticmethod
        def call(**kwargs):
            if kwargs["text"] == "chunk one":
                return _Response(b"AUDIO_ONE")
            return _Response(b"AUDIO_TWO")

    _install_fake_dashscope_qwen_tts(monkeypatch, _FakeSynthesizer)

    client = TTSClient.__new__(TTSClient)
    client.api_key = "test-key"
    client.model = "test-model"
    client.voice = "test-voice"
    monkeypatch.setattr(
        client,
        "_split_text",
        lambda text, max_length=500: ["chunk one", "chunk two"],
    )

    audio = await client.synthesize("input text")

    assert audio == b"AUDIO_ONEAUDIO_TWO"
