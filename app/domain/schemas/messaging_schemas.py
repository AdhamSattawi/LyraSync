from pydantic import BaseModel
from typing import Optional


class IncomingMessage(BaseModel):
    from_phone: str
    text: str
    audio_url: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    platform: str
    external_id: Optional[str] = None
