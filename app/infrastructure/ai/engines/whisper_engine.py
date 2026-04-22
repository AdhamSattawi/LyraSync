from openai import AsyncOpenAI
from app.infrastructure.ai.engines.base import (
    TranscriptionEngine,
    ChunkResult,
    TranscribedSegment,
)
from app.domain.exceptions.exceptions import AIError


class OpenAIWhisperEngine(TranscriptionEngine):
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    @property
    def name(self) -> str:
        return "OpenAI Whisper"

    @property
    def engine_id(self) -> str:
        return "whisper"

    async def transcribe_chunk(
        self,
        audio_path: str,
        language: str = "en",
    ) -> ChunkResult:
        """
        Transcribes a chunk using OpenAI's whisper-1 model.
        """
        try:
            with open(audio_path, "rb") as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                )

            # Response from OpenAI 'verbose_json' includes segments
            segments = []
            for seg in response.segments:
                segments.append(
                    TranscribedSegment(
                        start=seg["start"],
                        end=seg["end"],
                        text=seg["text"],
                        confidence=1.0,  # Whisper API doesn't provide per-segment confidence yet
                    )
                )

            return ChunkResult(
                segments=segments,
                language=response.language,
                duration=response.duration,
            )

        except Exception as e:
            raise AIError(f"Whisper transcription failed: {str(e)}")
