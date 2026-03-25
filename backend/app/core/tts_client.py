"""Alibaba Cloud DashScope TTS client."""

import base64
import io
import logging
import re
import time
import wave
from typing import AsyncGenerator, Optional

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


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
        from dashscope.audio.qwen_tts import SpeechSynthesizer

        dashscope.api_key = self.api_key

        sanitized_text = self._sanitize_text_for_tts(text)
        # Split text into chunks if too long
        chunks = self._split_text(sanitized_text, max_length=settings.tts_chunk_size)
        valid_chunks = [chunk for chunk in chunks if self._is_valid_tts_chunk(chunk)]
        audio_segments = []
        logger.info(
            "Starting TTS synthesis",
            extra={
                "model": self.model,
                "voice": self.voice,
                "text_chars": len(text),
                "sanitized_text_chars": len(sanitized_text),
                "chunk_count": len(chunks),
                "valid_chunk_count": len(valid_chunks),
            },
        )
        if not valid_chunks:
            logger.error(
                "TTS synthesis aborted: no valid chunks",
                extra={
                    "model": self.model,
                    "voice": self.voice,
                    "text_chars": len(text),
                },
            )
            raise RuntimeError("TTS error: no valid text chunks after sanitization")

        for i, chunk in enumerate(valid_chunks, start=1):
            chunk_start = time.monotonic()
            attempt_chunks = self._build_attempt_chunks(chunk)
            response_status = None
            response_message = ""
            audio_bytes = b""
            for attempt_idx, attempt_chunk in enumerate(attempt_chunks, start=1):
                response_status, response_message, audio_bytes = self._tts_call(
                    SpeechSynthesizer=SpeechSynthesizer,
                    chunk=attempt_chunk,
                )
                if response_status == 200:
                    break
                logger.warning(
                    "TTS chunk attempt failed",
                    extra={
                        "chunk_index": i,
                        "attempt": attempt_idx,
                        "attempts": len(attempt_chunks),
                        "chunk_chars": len(chunk),
                        "attempt_chunk_chars": len(attempt_chunk),
                        "status_code": response_status,
                        "error_message": response_message,
                    },
                )

            if response_status != 200:
                logger.error(
                    "Skipping invalid TTS chunk after retries",
                    extra={
                        "model": self.model,
                        "voice": self.voice,
                        "chunk_index": i,
                        "chunk_chars": len(chunk),
                        "attempts": len(attempt_chunks),
                    },
                )
                continue

            audio_segments.append(audio_bytes)
            logger.info(
                "TTS chunk synthesized",
                extra={
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    "chunk_chars": len(chunk),
                    "elapsed_seconds": round(time.monotonic() - chunk_start, 2),
                },
            )

        logger.info(
            "TTS synthesis completed",
            extra={
                "chunk_count": len(chunks),
                "audio_segments": len(audio_segments),
            },
        )
        if not audio_segments:
            raise RuntimeError("TTS error: all chunks failed to synthesize")
        return self._concatenate_audio_segments(audio_segments)

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

    def _tts_call(self, SpeechSynthesizer, chunk: str) -> tuple[int, str, bytes]:
        """Invoke DashScope Qwen TTS call for one chunk."""
        response = SpeechSynthesizer.call(
            model=self.model,
            text=chunk,
            voice=self.voice,
            stream=True,
        )
        if isinstance(response, (bytes, bytearray, str, dict)) or not hasattr(
            response, "__iter__"
        ):
            parts = [response]
        else:
            parts = response

        audio_buffer = bytearray()
        status = 500
        message = "Unknown TTS response"
        for part in parts:
            status = int(getattr(part, "status_code", 500))
            message = str(getattr(part, "message", ""))
            if status != 200:
                return status, message, b""
            output = getattr(part, "output", None)
            if output is None or "audio" not in output:
                continue
            audio_payload = output["audio"]
            if isinstance(audio_payload, (bytes, bytearray)):
                audio_buffer.extend(audio_payload)
                continue
            if isinstance(audio_payload, dict):
                data = audio_payload.get("data")
                if data:
                    audio_buffer.extend(base64.b64decode(data))

        if not audio_buffer:
            return 500, "No audio data in streaming response", b""
        return 200, "", self._ensure_mp3_bytes(bytes(audio_buffer))

    @staticmethod
    def _ensure_mp3_bytes(audio_bytes: bytes) -> bytes:
        """Return audio bytes as-is when already playable."""
        if not audio_bytes:
            raise RuntimeError("Empty audio bytes")

        # MP3 starts with ID3 header or frame sync.
        if audio_bytes.startswith(b"ID3") or audio_bytes[:2] == b"\xff\xfb":
            return audio_bytes

        # Keep WAV data unchanged if provider returns RIFF/WAV bytes.
        if audio_bytes.startswith(b"RIFF"):
            return audio_bytes

        return audio_bytes

    @staticmethod
    def _is_wav_bytes(audio_bytes: bytes) -> bool:
        """Check whether payload appears to be RIFF/WAV."""
        return bool(audio_bytes and audio_bytes.startswith(b"RIFF"))

    def _concatenate_audio_segments(self, audio_segments: list[bytes]) -> bytes:
        """Concatenate synthesized chunk payloads into one audio blob."""
        if not audio_segments:
            raise RuntimeError("No synthesized audio segments to concatenate")
        if len(audio_segments) == 1:
            return audio_segments[0]

        all_wav = all(self._is_wav_bytes(segment) for segment in audio_segments)
        if all_wav:
            return self._concatenate_wav_segments(audio_segments)

        # Prefer decode/re-encode path so duration metadata reflects full content.
        try:
            from pydub import AudioSegment

            combined = AudioSegment.empty()
            for segment in audio_segments:
                segment_format = "wav" if self._is_wav_bytes(segment) else "mp3"
                combined += AudioSegment.from_file(io.BytesIO(segment), format=segment_format)

            output = io.BytesIO()
            combined.export(output, format="mp3")
            return output.getvalue()
        except Exception:
            logger.warning(
                "Audio segment decode failed, using raw byte concatenation fallback",
                extra={"audio_segments": len(audio_segments)},
            )
            return b"".join(audio_segments)

    @staticmethod
    def _concatenate_wav_segments(audio_segments: list[bytes]) -> bytes:
        """Concatenate WAV byte streams while preserving PCM params."""
        with wave.open(io.BytesIO(audio_segments[0]), "rb") as first_wav:
            params = first_wav.getparams()
            frames = [first_wav.readframes(first_wav.getnframes())]

        for segment in audio_segments[1:]:
            with wave.open(io.BytesIO(segment), "rb") as wav_file:
                current = wav_file.getparams()
                if (
                    current.nchannels != params.nchannels
                    or current.sampwidth != params.sampwidth
                    or current.framerate != params.framerate
                ):
                    raise RuntimeError("Incompatible WAV chunk format from TTS provider")
                frames.append(wav_file.readframes(wav_file.getnframes()))

        output = io.BytesIO()
        with wave.open(output, "wb") as out_wav:
            out_wav.setnchannels(params.nchannels)
            out_wav.setsampwidth(params.sampwidth)
            out_wav.setframerate(params.framerate)
            for frame_chunk in frames:
                out_wav.writeframes(frame_chunk)
        return output.getvalue()

    def _sanitize_text_for_tts(self, text: str) -> str:
        """Remove markdown/noise that commonly breaks TTS requests."""
        cleaned = text or ""
        cleaned = re.sub(r"```.*?```", " ", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
        cleaned = re.sub(r"https?://\S+", " ", cleaned)
        cleaned = re.sub(r"^\s{0,3}[#>*-]+\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", cleaned)
        cleaned = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _is_valid_tts_chunk(chunk: str) -> bool:
        """Require chunks to have enough natural-language content."""
        if not chunk:
            return False
        compact = chunk.strip()
        if len(compact) < 4:
            return False
        return bool(re.search(r"[A-Za-z0-9]{3,}", compact))

    def _build_fallback_chunk(self, chunk: str) -> str:
        """Build simpler fallback text for retrying invalid chunks."""
        simplified = re.sub(r"[^A-Za-z0-9\s,.;:!?'-]", " ", chunk)
        simplified = re.sub(r"\s+", " ", simplified).strip()
        if not self._is_valid_tts_chunk(simplified):
            return ""
        return simplified

    def _build_attempt_chunks(self, chunk: str) -> list[str]:
        """Return ordered chunk variants to improve TTS success rate."""
        attempts: list[str] = []
        if self._is_valid_tts_chunk(chunk):
            attempts.append(chunk)

        fallback = self._build_fallback_chunk(chunk)
        if fallback and fallback not in attempts:
            attempts.append(fallback)

        # Last-resort generic safe sentence to avoid failing the entire section.
        generic = "This section explains key parts of the repository."
        if generic not in attempts:
            attempts.append(generic)

        return attempts
