"""Audio processing and assembly module."""

import uuid
import logging
import time
import wave
from pathlib import Path
from typing import Callable, Optional

from app.config import get_settings
from app.core.tts_client import TTSClient
from app.models.schemas import Chapter, GeneratedScript

settings = get_settings()
logger = logging.getLogger(__name__)


class AudioProcessor:
    """Processes and assembles audio for podcasts."""

    def __init__(self):
        self.tts_client = TTSClient()

    async def synthesize(
        self,
        script: GeneratedScript,
        output_dir: Path,
        podcast_id: str,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> dict:
        """
        Synthesize script to audio with chapter markers.

        Returns dict with audio_path, chapters, and duration.
        """
        # Collect all text to synthesize
        text_parts = []
        logger.info(
            "Starting audio synthesis pipeline",
            extra={
                "podcast_id": podcast_id,
                "output_dir": str(output_dir),
                "sections": len(script.sections),
            },
        )

        # Introduction
        if script.introduction:
            text_parts.append(("Introduction", script.introduction))

        # Sections
        for section in script.sections:
            text_parts.append((section.title, section.content))

        # Conclusion
        if script.conclusion:
            text_parts.append(("Conclusion", script.conclusion))

        # Synthesize each part
        audio_segments = []
        chapters = []
        current_time = 0.0

        total_parts = len(text_parts)
        logger.info(
            "Prepared script parts for synthesis",
            extra={
                "podcast_id": podcast_id,
                "total_parts": total_parts,
            },
        )
        for i, (title, content) in enumerate(text_parts):
            if on_progress:
                on_progress(i / total_parts)

            # Synthesize this section
            section_start = time.monotonic()
            logger.info(
                "Synthesizing section",
                extra={
                    "podcast_id": podcast_id,
                    "section_index": i + 1,
                    "total_parts": total_parts,
                    "title": title,
                    "content_chars": len(content),
                },
            )
            audio_data = await self.tts_client.synthesize(content)

            # Save segment
            segment_ext = ".wav" if self._is_wav_bytes(audio_data) else ".mp3"
            segment_path = output_dir / f"{podcast_id}_{i}{segment_ext}"
            segment_path.write_bytes(audio_data)

            # Get segment duration
            duration = self._get_audio_duration(segment_path)

            # Track chapter info
            chapters.append(
                Chapter(
                    id=len(chapters) + 1,
                    title=title,
                    start_time=current_time,
                    end_time=current_time + duration,
                )
            )

            audio_segments.append(segment_path)
            current_time += duration
            logger.info(
                "Section synthesized",
                extra={
                    "podcast_id": podcast_id,
                    "section_index": i + 1,
                    "total_parts": total_parts,
                    "title": title,
                    "duration_seconds": round(duration, 2),
                    "elapsed_seconds": round(time.monotonic() - section_start, 2),
                },
            )

        # Concatenate all segments
        output_ext = ".wav" if audio_segments and all(p.suffix == ".wav" for p in audio_segments) else ".mp3"
        output_path = output_dir / f"{podcast_id}{output_ext}"
        concat_start = time.monotonic()
        self._concatenate_audio(audio_segments, output_path)
        logger.info(
            "Audio segments concatenated",
            extra={
                "podcast_id": podcast_id,
                "segments": len(audio_segments),
                "output_path": str(output_path),
                "elapsed_seconds": round(time.monotonic() - concat_start, 2),
            },
        )

        # Clean up segment files
        for segment_path in audio_segments:
            segment_path.unlink(missing_ok=True)

        # Add chapter markers to MP3
        self._add_chapter_markers(output_path, chapters)
        logger.info(
            "Audio synthesis pipeline completed",
            extra={
                "podcast_id": podcast_id,
                "chapters": len(chapters),
                "duration_seconds": round(current_time, 2),
                "audio_path": str(output_path),
            },
        )

        return {
            "audio_path": str(output_path),
            "chapters": chapters,
            "duration": current_time,
        }

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of an audio file in seconds."""
        if audio_path.suffix.lower() == ".wav":
            try:
                with wave.open(str(audio_path), "rb") as wav_file:
                    frames = wav_file.getnframes()
                    frame_rate = wav_file.getframerate()
                    return frames / float(frame_rate)
            except Exception:
                pass
        try:
            from mutagen.mp3 import MP3
            audio = MP3(str(audio_path))
            return audio.info.length
        except Exception:
            # Fallback: estimate based on file size
            # Roughly 1MB per minute for 128kbps MP3
            file_size = audio_path.stat().st_size
            return (file_size / (1024 * 1024)) * 60

    def _concatenate_audio(self, segments: list[Path], output: Path):
        """Concatenate audio segments into one file."""
        if output.suffix.lower() == ".wav" and all(s.suffix.lower() == ".wav" for s in segments):
            self._concatenate_wav(segments, output)
            return
        try:
            from pydub import AudioSegment

            combined = AudioSegment.empty()
            for segment in segments:
                audio = AudioSegment.from_mp3(str(segment))
                combined += audio

            combined.export(str(output), format="mp3")
        except Exception:
            # Fallback: use ffmpeg directly
            import subprocess

            # Create file list for ffmpeg
            list_file = output.parent / f"{output.stem}_list.txt"
            with open(list_file, "w") as f:
                for segment in segments:
                    f.write(f"file '{segment}'\n")

            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                str(output),
                "-y",
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            list_file.unlink(missing_ok=True)

    @staticmethod
    def _is_wav_bytes(audio_data: bytes) -> bool:
        """Check whether byte payload is RIFF/WAV."""
        return bool(audio_data and audio_data.startswith(b"RIFF"))

    @staticmethod
    def _concatenate_wav(segments: list[Path], output: Path):
        """Concatenate WAV files using Python stdlib only."""
        if not segments:
            raise ValueError("No segments provided")

        with wave.open(str(segments[0]), "rb") as first_wav:
            params = first_wav.getparams()
            frames = [first_wav.readframes(first_wav.getnframes())]

        for segment in segments[1:]:
            with wave.open(str(segment), "rb") as wav_file:
                current = wav_file.getparams()
                if (
                    current.nchannels != params.nchannels
                    or current.sampwidth != params.sampwidth
                    or current.framerate != params.framerate
                ):
                    raise ValueError("Incompatible WAV segment format for concatenation")
                frames.append(wav_file.readframes(wav_file.getnframes()))

        with wave.open(str(output), "wb") as out_wav:
            out_wav.setnchannels(params.nchannels)
            out_wav.setsampwidth(params.sampwidth)
            out_wav.setframerate(params.framerate)
            for frame_chunk in frames:
                out_wav.writeframes(frame_chunk)

    def _add_chapter_markers(self, audio_path: Path, chapters: list[Chapter]):
        """Add ID3 chapter markers to MP3 file."""
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, CHAP, TIT2

            audio = MP3(str(audio_path))

            # Ensure ID3 tags exist
            if audio.tags is None:
                audio.add_tags()

            # Add chapter frames
            for chapter in chapters:
                # Convert seconds to milliseconds
                start_ms = int(chapter.start_time * 1000)
                end_ms = int(chapter.end_time * 1000)

                chap_frame = CHAP(
                    element_id=f"chapter{chapter.id}".encode(),
                    start_time=start_ms,
                    end_time=end_ms,
                    sub_frames=[TIT2(text=chapter.title)],
                )
                audio.tags.add(chap_frame)

            audio.save()
        except Exception:
            # Chapter markers are optional, don't fail if this doesn't work
            pass
