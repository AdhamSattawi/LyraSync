import asyncio
import logging
from pathlib import Path
import httpx

from app.core.config import settings
from app.infrastructure.ai.engines.base import (
    TranscriptionEngine,
    ChunkResult,
    TranscribedSegment,
)
from app.domain.exceptions.exceptions import AIError

logger = logging.getLogger(__name__)

HF_INFERENCE_URL = "https://api-inference.huggingface.co/models"
IVRIT_MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"


class IvritEngine(TranscriptionEngine):
    """
    Hebrew-optimized transcription via HuggingFace Inference API.
    """

    def __init__(self, api_key: str, model: str = IVRIT_MODEL):
        self.api_key = api_key
        self.model = model

    @property
    def name(self) -> str:
        return f"ivrit-ai ({self.model})"

    @property
    def engine_id(self) -> str:
        return "ivrit"

    async def transcribe_chunk(
        self,
        audio_path: str,
        language: str = "he",
    ) -> ChunkResult:
        """
        Transcribes a chunk using ivrit-ai models on HuggingFace.
        """
        if not self.api_key:
            raise AIError("HuggingFace API key not set.")

        try:
            audio_file = Path(audio_path)
            audio_bytes = audio_file.read_bytes()

            url = f"{HF_INFERENCE_URL}/{self.model}"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    content=audio_bytes,
                    params={"wait_for_model": "true"},
                )

            # Handle model loading (503)
            if response.status_code == 503:
                logger.info(f"Ivrit model {self.model} is loading, waiting...")
                await asyncio.sleep(20)
                async with httpx.AsyncClient(timeout=180.0) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        content=audio_bytes,
                        params={"wait_for_model": "true"},
                    )

            if response.status_code != 200:
                raise AIError(f"Ivrit API error {response.status_code}: {response.text}")

            data = response.json()

            # Parse response — HF ASR returns {"text": "..."} or {"chunks": [...]}
            if isinstance(data, dict):
                text = data.get("text", "")
                chunks = data.get("chunks", [])

                if chunks:
                    segments = []
                    for chunk in chunks:
                        ts = chunk.get("timestamp", [0, 0])
                        segments.append(
                            TranscribedSegment(
                                start=ts[0] if ts[0] is not None else 0,
                                end=ts[1] if ts[1] is not None else 0,
                                text=chunk.get("text", "").strip(),
                                confidence=0.9,
                            )
                        )
                    return ChunkResult(segments=segments, language=language)

                # Fallback to simple text response
                return ChunkResult(
                    segments=[TranscribedSegment(start=0, end=30, text=text.strip())],
                    language=language,
                )

            raise AIError(f"Unexpected Ivrit response format: {type(data)}")

        except Exception as e:
            if isinstance(e, AIError):
                raise
            raise AIError(f"Ivrit transcription failed: {str(e)}")
