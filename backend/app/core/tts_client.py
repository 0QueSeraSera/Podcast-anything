"""Alibaba Cloud DashScope TTS client."""

import asyncio
from typing import AsyncGenerator, Optional

from app.config import get_settings

settings = get_settings()


class TTSClient:
    """Client for Alibaba Cloud DashScope TTS."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.dashscope_api_key
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not configured")

        self.model = settings.tts_model
        self.voice = settings.tts_voice

    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech from text.

        Returns audio bytes (MP3 format).
        """
        import dashscope
        from dashscope import MultiModalConversation

        dashscope.api_key = self.api_key

        # Split text into chunks if too long
        chunks = self._split_text(text)
        audio_segments = []

        for chunk in chunks:
            response = MultiModalConversation.call(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"text": chunk},
                        ],
                    }
                ],
                voice=self.voice,
            )

            if response.status_code != 200:
                raise RuntimeError(f"TTS error: {response.message}")

            # Extract audio from response
            if hasattr(response, "output") and "audio" in response.output:
                audio_segments.append(response.output["audio"])

        # For now, return the first segment
        # In production, concatenate all segments
        return audio_segments[0] if audio_segments else b""

    async def synthesize_stream(
        self, text: str
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize speech with streaming.

        Yields audio chunks as they're generated.
        """
        import dashscope
        from dashscope import MultiModalConversation

        dashscope.api_key = self.api_key

        chunks = self._split_text(text)

        for chunk in chunks:
            responses = MultiModalConversation.call(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": chunk}],
                    }
                ],
                voice=self.voice,
                stream=True,
            )

            for response in responses:
                if response.status_code == 200:
                    if hasattr(response, "output") and "audio" in response.output:
                        yield response.output["audio"]

    def _split_text(self, text: str, max_length: int = 500) -> list[str]:
        """
        Split text into chunks for TTS.

        Tries to split on sentence boundaries.
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""

        # Split on sentence boundaries
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
