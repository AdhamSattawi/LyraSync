from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel
import uuid
from app.domain.schemas.intent_schema import IntentType


class IntentHandler(ABC):
    @property
    @abstractmethod
    def intent_type(self) -> IntentType:
        """The intent this handler serves"""
        pass

    @property
    @abstractmethod
    def extraction_schema(self) -> Type[BaseModel] | None:
        """The Pydantic schema the LLM must fill. Return None if no schema needed."""
        pass

    @abstractmethod
    def get_system_prompt(self, profession: str) -> str:
        """Return the dynamic system prompt used for LLM extraction."""
        pass

    @abstractmethod
    async def execute(
        self,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        extracted_data: BaseModel | None,
    ) -> str:
        """Execute the business logic and return the human-readable string."""
        pass
