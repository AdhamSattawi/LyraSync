from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class TranscribedSegment:
    """A segment (sentence/phrase) of transcribed text."""
    start: float
    end: float
    text: str
    confidence: float = 1.0


@dataclass
class ChunkResult:
    """Result from transcribing a single audio chunk."""
    segments: list[TranscribedSegment]
    language: str
    duration: float = 0.0

    @property
    def full_text(self) -> str:
        return " ".join([s.text for s in self.segments]).strip()


@runtime_checkable
class TranscriptionEngine(Protocol):
    """Protocol that all transcription engines must implement."""

    @property
    def name(self) -> str:
        """Human-readable engine name (e.g., 'OpenAI Whisper')."""
        ...

    @property
    def engine_id(self) -> str:
        """Machine identifier (e.g., 'whisper' | 'ivrit')."""
        ...

    async def transcribe_chunk(
        self,
        audio_path: str,
        language: str = "en",
    ) -> ChunkResult:
        """Transcribe a single audio file path."""
        ...
