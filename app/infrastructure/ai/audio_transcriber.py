import os
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from app.infrastructure.ai.engines.base import TranscriptionEngine, ChunkResult, TranscribedSegment
from app.infrastructure.ai.audio_processor import AudioProcessor
from app.domain.exceptions.exceptions import AIError


class AudioTranscriber(ABC):
    @abstractmethod
    async def transcribe(
        self, file_data: str | bytes, language: str = "en", vocabulary: list[str] | None = None
    ) -> str:
        """Transcribes audio from a file path or raw bytes."""
        raise NotImplementedError


class LLMDataTranscriber(AudioTranscriber):
    """
    Production-grade transcriber that coordinates audio processing,
    chunking, and engine-agnostic transcription.
    """

    def __init__(
        self,
        engines: dict[str, TranscriptionEngine],
        default_engine_id: str = "whisper",
        processor: Optional[AudioProcessor] = None,
    ):
        self.engines = engines
        self.default_engine_id = default_engine_id
        self.processor = processor or AudioProcessor()

    async def transcribe(
        self,
        file_data: str | bytes,
        language: str = "en",
        vocabulary: list[str] | None = None,
    ) -> str:
        # Determine engine based on language
        # For now: "he" -> "ivrit", others -> "whisper"
        engine_id = "ivrit" if language == "he" else "whisper"
        engine = self.engines.get(engine_id) or self.engines.get(self.default_engine_id)

        if not engine:
            raise AIError(f"No transcription engine found for language: {language}")

        temp_paths = []
        try:
            # 1. Prepare local file
            if isinstance(file_data, bytes):
                # Write bytes to temp file for processing
                input_path = self.processor.working_dir / f"input_{os.urandom(4).hex()}.ogg"
                with open(input_path, "wb") as f:
                    f.write(file_data)
                temp_paths.append(input_path)
            else:
                input_path = Path(file_data)

            # 2. Convert to standard WAV (16kHz Mono)
            wav_path = await self.processor.convert_to_wav(input_path)
            temp_paths.append(wav_path)

            # 3. Split into 30s chunks with 2s overlap
            # Returns list of (chunk_path, offset)
            chunks = await self.processor.split_into_chunks(wav_path, chunk_duration=30, overlap=2)
            chunk_paths = [c[0] for c in chunks]
            temp_paths.extend(chunk_paths)

            # 4. Transcribe each chunk in parallel [SCALE-03]
            async def transcribe_with_offset(path, offset):
                res = await engine.transcribe_chunk(str(path), language=language)
                return (res, offset)

            tasks = [transcribe_with_offset(path, offset) for path, offset in chunks]
            chunk_results: List[tuple[ChunkResult, float]] = await asyncio.gather(*tasks)

            # 5. Merge results (Overlap-aware merging logic)
            full_text = self._merge_results(chunk_results, overlap_duration=2.0)
            return full_text

        except Exception as e:
            raise AIError(f"Transcription workflow failed: {str(e)}")
        finally:
            # 6. Cleanup all temp files
            self.processor.cleanup(temp_paths)

    def _merge_results(self, chunk_data: List[tuple[ChunkResult, float]], overlap_duration: float) -> str:
        """
        Merges transcription results from overlapping chunks.
        """
        if not chunk_data:
            return ""
        if len(chunk_data) == 1:
            return chunk_data[0][0].full_text

        all_text_segments = []
        
        for i, (result, offset) in enumerate(chunk_data):
            for segment in result.segments:
                # Absolute timestamps
                start_abs = segment.start + offset
                end_abs = segment.end + offset
                
                # If not the first chunk, skip segments that are purely in the overlap zone
                if i > 0:
                    overlap_end = offset + overlap_duration
                    if end_abs <= overlap_end:
                        continue
                    # If segment partially overlaps, we keep it but the simple 
                    # logic here is to just append non-duplicates.
                
                all_text_segments.append(segment.text.strip())

        # Basic deduplication of exact adjacent strings (common in overlap)
        deduped = []
        for text in all_text_segments:
            if not deduped or text != deduped[-1]:
                deduped.append(text)
                
        return " ".join(deduped).strip()
