from app.domain.models.message import Message
from app.infrastructure.database.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self):
        super().__init__(Message)
