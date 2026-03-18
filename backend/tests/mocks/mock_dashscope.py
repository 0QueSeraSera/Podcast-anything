"""Mock for DashScope TTS API calls."""

from typing import Any
from unittest.mock import MagicMock, patch


class MockDashScopeResponse:
    """Mock response from DashScope API."""

    def __init__(
        self,
        status_code: int = 200,
        audio_data: bytes = b"mock_audio_data",
        message: str = "Success",
    ):
        self.status_code = status_code
        self.message = message
        self._audio_data = audio_data

    @property
    def output(self) -> dict[str, Any]:
        if self.status_code == 200:
            return {"audio": self._audio_data}
        return {}

    def __iter__(self):
        """Make it iterable for streaming responses."""
        yield self


class MockMultiModalConversation:
    """Mock for DashScope MultiModalConversation class."""

    _last_call_params: dict[str, Any] = {}

    @classmethod
    def call(
        cls,
        model: str,
        messages: list[dict],
        voice: str = "Cherry",
        stream: bool = False,
        **kwargs,
    ) -> MockDashScopeResponse:
        """Mock the call method."""
        cls._last_call_params = {
            "model": model,
            "messages": messages,
            "voice": voice,
            "stream": stream,
            **kwargs,
        }

        # Generate mock audio based on text length
        text = messages[0]["content"][0]["text"] if messages else ""
        audio_size = len(text) * 100  # Fake audio size proportional to text
        mock_audio = b"MOCK_AUDIO_" + bytes([0] * audio_size)

        return MockDashScopeResponse(audio_data=mock_audio)

    @classmethod
    def get_last_call_params(cls) -> dict[str, Any]:
        """Get parameters from the last call (for assertions)."""
        return cls._last_call_params.copy()


def patch_dashscope():
    """Patch DashScope module for testing."""
    mock_module = MagicMock()
    mock_module.MultiModalConversation = MockMultiModalConversation
    mock_module.api_key = None

    return patch.dict("sys.modules", {"dashscope": mock_module})


class MockTTSClient:
    """Mock TTSClient for testing without actual API calls."""

    def __init__(self, api_key: str = "test-key"):
        self.api_key = api_key
        self.model = "test-model"
        self.voice = "test-voice"

    async def synthesize(self, text: str) -> bytes:
        """Mock synthesize method."""
        # Return fake audio data proportional to text length
        return b"MOCK_AUDIO_" + bytes([0] * len(text) * 100)

    async def synthesize_stream(self, text: str):
        """Mock synthesize_stream method."""
        chunks = self._split_text(text)
        for chunk in chunks:
            yield b"MOCK_CHUNK_" + chunk.encode()[:50]

    def _split_text(self, text: str, max_length: int = 500) -> list[str]:
        """Split text into chunks (mirrors real implementation)."""
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""
        sentences = text.replace("\n", " ").split(". ")

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


def create_mock_tts_client():
    """Create a mock TTSClient instance."""
    return MockTTSClient()
