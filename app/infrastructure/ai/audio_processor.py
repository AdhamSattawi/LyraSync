import asyncio
import json
import logging
import os
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Handles all ffmpeg operations: probe, convert, and split into chunks.
    Inspired by BlitzAI.
    """

    def __init__(self, working_dir: str = "/tmp/lyrasync_audio"):
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)

    async def probe_audio(self, file_path: str | Path) -> dict:
        """Get audio file metadata using ffprobe."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(file_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {stderr.decode()}")

        info = json.loads(stdout.decode())
        duration = float(info.get("format", {}).get("duration", 0))

        return {
            "duration": duration,
            "format": info.get("format", {}).get("format_name", "unknown"),
        }

    async def convert_to_wav(self, input_path: str | Path) -> Path:
        """
        Convert any audio to WAV 16kHz mono (Standard for transcription).
        """
        input_path = Path(input_path)
        output_path = self.working_dir / f"{uuid.uuid4().hex}.wav"

        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",  # Mono
            str(output_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed: {stderr.decode()}")

        return output_path

    async def split_into_chunks(
        self, wav_path: str | Path, chunk_duration: int = 30, overlap: int = 2
    ) -> list[tuple[Path, float]]:
        """
        Split a WAV file into chunks with overlap for context continuity.
        Returns list of (chunk_path, offset_seconds).
        """
        wav_path = Path(wav_path)
        info = await self.probe_audio(wav_path)
        total_duration = info["duration"]

        if total_duration <= chunk_duration:
            return [(wav_path, 0.0)]

        chunks = []
        start = 0.0
        chunk_idx = 0

        while start < total_duration:
            end = min(start + chunk_duration, total_duration)
            chunk_filename = f"{wav_path.stem}_chunk_{chunk_idx:04d}.wav"
            chunk_path = self.working_dir / chunk_filename

            cmd = [
                "ffmpeg", "-y",
                "-i", str(wav_path),
                "-ss", str(start),
                "-t", str(end - start),
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(chunk_path),
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode == 0:
                chunks.append((chunk_path, start))

            chunk_idx += 1
            # Step forward but leave overlap
            start += chunk_duration - overlap

        return chunks

    def cleanup(self, paths: list[Path]):
        """Remove temporary files."""
        for p in paths:
            if p.exists():
                try:
                    os.remove(p)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {p}: {e}")
