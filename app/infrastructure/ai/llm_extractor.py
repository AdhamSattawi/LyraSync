from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.domain.exceptions.exceptions import AIAnalysisError

T = TypeVar("T", bound=BaseModel)


class DataExtractor(ABC):
    @abstractmethod
    async def extract(self, transcript: str, schema: Type[T], system_prompt: str) -> T:
        raise NotImplementedError


class LLMDataExtractor(DataExtractor):
    def __init__(self, client: AsyncOpenAI) -> None:
        self.client = client

    async def extract(self, transcript: str, schema: Type[T], system_prompt: str) -> T:
        response = await self.client.beta.chat.completions.parse(
            model="gpt-5.4-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
            response_format=schema,
        )
        message = response.choices[0].message
        if message.refusal:
            raise AIAnalysisError(f"AI refused to extract data: {message.refusal}")
        return message.parsed
