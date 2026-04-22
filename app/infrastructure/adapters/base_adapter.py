from abc import ABC, abstractmethod
from fastapi import Request
from app.domain.schemas.messaging_schemas import IncomingMessage


class BaseMessageAdapter(ABC):
    @abstractmethod
    async def parse_incoming(self, request: Request) -> IncomingMessage:
        pass

    @abstractmethod
    async def send_reply(
        self, to_phone: str, text: str, media_url: str | None = None
    ) -> None:
        """
        Send a reply message to the user.

        Args:
            to_phone: The recipient's phone number.
            text: The text body of the message.
            media_url: Optional URL to a media file (PDF, image, etc.) to attach.
        """
        pass
