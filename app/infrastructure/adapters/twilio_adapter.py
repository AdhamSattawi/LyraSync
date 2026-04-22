import os
import asyncio
import httpx
import aiofiles
from fastapi import Request
from twilio.rest import Client
from app.core.config import settings
from app.domain.schemas.messaging_schemas import IncomingMessage
from app.infrastructure.adapters.base_adapter import BaseMessageAdapter


class TwilioWhatsappAdapter(BaseMessageAdapter):
    MEDIA_DIR = "/tmp/twilio_media/whatsapp"

    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        os.makedirs(self.MEDIA_DIR, exist_ok=True)

    async def parse_incoming(self, request: Request) -> IncomingMessage:
        data = await request.form()
        from_phone = data.get("From", "").replace("whatsapp:", "")
        body = data.get("Body", "")
        num_media = int(data.get("NumMedia", 0))
        raw_audio_url = data.get("MediaUrl0") if num_media > 0 else None
        message_sid = data.get("MessageSid") or data.get("SmsSid")

        # Download audio to disk and store the local path and bytes
        local_audio_path: str | None = None
        audio_bytes: bytes | None = None
        
        if raw_audio_url:
            local_audio_path, audio_bytes = await self._download_media(raw_audio_url, from_phone)

        return IncomingMessage(
            from_phone=from_phone,
            text=body,
            audio_url=local_audio_path,  # local /tmp path
            audio_bytes=audio_bytes,
            platform="twilio_whatsapp",
            external_id=message_sid,
        )

    async def _download_media(self, url: str, from_phone: str) -> tuple[str | None, bytes | None]:
        """Downloads Twilio media to /tmp and returns the local filepath and bytes."""
        try:
            # Twilio requires Basic Auth even for media downloads
            auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            filename = (
                f"twilio_{from_phone.replace('+', '')}_{os.path.basename(url)}.ogg"
            )
            filepath = os.path.join(self.MEDIA_DIR, filename)

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, auth=auth, follow_redirects=True)
                resp.raise_for_status()
                content = resp.content
                
                # Non-blocking write to temp file [QUALITY-02]
                async with aiofiles.open(filepath, mode="wb") as f:
                    await f.write(content)

            return filepath, content
        except Exception as e:
            print(f"[TwilioWhatsappAdapter] Failed to download media: {e}")
            return None, None

    async def send_reply(
        self, to_phone: str, text: str, media_url: str | None = None
    ) -> None:
        """Sends a WhatsApp message via Twilio SDK.

        The Twilio SDK is synchronous, so we run it in a thread pool to avoid
        blocking the FastAPI async event loop.

        If media_url is provided, Twilio attaches it as a WhatsApp media message
        (the PDF will appear inline in the conversation).
        """
        kwargs = dict(
            to=f"whatsapp:{to_phone}",
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            body=text,
        )
        if media_url:
            kwargs["media_url"] = [media_url]

        await asyncio.to_thread(self.client.messages.create, **kwargs)
