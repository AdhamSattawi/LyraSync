import os
import uuid
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import Response

from app.infrastructure.adapters.twilio_adapter import TwilioWhatsappAdapter
from app.api.dependencies import (
    get_agent_dispatcher,
    get_twilio_whatsapp_adapter,
    get_storage_service,
    validate_twilio_request,
    get_db,
    logger,
    limiter,
)
from app.services.agent_dispatcher import AgentDispatcher
from app.domain.schemas.handler_reply import HandlerReply
from app.domain.models.message import MessageDirection
from app.infrastructure.storage.storage_service import StorageService
from app.infrastructure.database.repositories.webhook_repository import WebhookRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def send_and_log_reply(
    adapter: TwilioWhatsappAdapter,
    dispatcher: AgentDispatcher,
    to_phone: str,
    text: str,
    media_url: str | None,
    user_id: uuid.UUID | None,
    business_id: uuid.UUID | None,
):
    """
    Sends a reply via Twilio and logs it to the database.
    """
    # 1. Send the reply
    try:
        await adapter.send_reply(to_phone, text, media_url=media_url)
    except Exception as e:
        logger.error(f"Error sending reply to {to_phone}: {e}")

    # 2. Log the outgoing message
    try:
        # Note: Twilio phone is our 'from' for outgoing
        # For MVP, using 'LyraSync' as the from_phone for outgoing
        await dispatcher.log_message(
            from_phone="LyraSync",
            to_phone=to_phone,
            content=text,
            media_url=media_url,
            direction=MessageDirection.OUTGOING,
            user_id=user_id,
            business_id=business_id,
        )
    except Exception as e:
        logger.error(f"Error logging outgoing message: {e}")


@router.post("/twilio/whatsapp", dependencies=[Depends(validate_twilio_request)])
@limiter.limit("10/minute")
async def webhook_twilio_whatsapp(
    request: Request,
    background_tasks: BackgroundTasks,
    adapter: TwilioWhatsappAdapter = Depends(get_twilio_whatsapp_adapter),
    dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
    storage_service: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Receives incoming WhatsApp messages from Twilio and routes them through
    the AgentDispatcher.
    """
    incoming_phone = None
    reply_text = "I'm having trouble right now. Please try again in a moment."
    reply_media_url: str | None = None
    audio_local_path: str | None = None
    persistent_audio_url: str | None = None
    user_id: uuid.UUID | None = None
    business_id: uuid.UUID | None = None

    try:
        incoming = await adapter.parse_incoming(request=request)
        incoming_phone = incoming.from_phone
        
        # ── Idempotency Check [INFRA-01] ────────────────────────────────────
        webhook_repo = WebhookRepository()
        if incoming.external_id:
            if await webhook_repo.is_processed(incoming.external_id, db):
                logger.info(f"Ignoring duplicate Twilio webhook: {incoming.external_id}")
                return Response(status_code=200)
            
            await webhook_repo.mark_as_processed(
                webhook_id=incoming.external_id,
                provider="twilio",
                payload={"from": incoming_phone},
                session=db
            )
            await db.commit()

    except Exception as e:
        logger.error(f"Error parsing incoming message: {type(e).__name__}: {e}")
        return Response(status_code=200)

    # ── Upload Audio to Persistent Storage [STORAGE-01] ──────────────────
    if incoming.audio_bytes:
        try:
            # Path convention: audio/incoming/{phone}/{uuid}.ogg
            destination = f"audio/incoming/{incoming_phone.replace('+', '')}/{uuid.uuid4().hex}.ogg"
            persistent_audio_url = await storage_service.upload(
                file_bytes=incoming.audio_bytes,
                destination_path=destination,
                content_type="audio/ogg"
            )
            logger.info(f"Uploaded incoming audio to {persistent_audio_url}")
        except Exception as e:
            logger.error(f"Failed to upload incoming audio to storage: {e}")

    # ── Log Incoming Message ───────────────────────────────────────────
    try:
        await dispatcher.log_message(
            from_phone=incoming_phone,
            to_phone="LyraSync",
            content=incoming.text,
            media_url=persistent_audio_url or incoming.audio_url, # Prefer persistent URL
            direction=MessageDirection.INCOMING,
        )
    except Exception as e:
        logger.error(f"Error logging incoming message: {e}")

    try:
        audio_local_path = incoming.audio_url
        is_audio = incoming.audio_url is not None
        # Transcriber can handle path or bytes
        message_content = incoming.audio_url if is_audio else incoming.text

        result = await dispatcher.process_message(
            user_phone=incoming_phone,
            message=message_content,
            is_audio=is_audio,
        )

        # Dispatcher returns a DispatcherResult object
        user_id = result.user_id
        business_id = result.business_id
        
        if isinstance(result.reply, HandlerReply):
            reply_text = result.reply.text
            reply_media_url = result.reply.media_url
        else:
            reply_text = result.reply

    except Exception as e:
        logger.exception(f"Error processing message: {type(e).__name__}: {e}")
        reply_text = "I'm having trouble right now. Please try again in a moment."

    finally:
        if audio_local_path and os.path.exists(audio_local_path):
            try:
                os.remove(audio_local_path)
            except Exception as e:
                logger.error(f"Error cleaning up audio file: {type(e).__name__}: {e}")

    # Offload send and log to background tasks
    background_tasks.add_task(
        send_and_log_reply,
        adapter,
        dispatcher,
        incoming_phone,
        reply_text,
        reply_media_url,
        user_id,
        business_id,
    )

    return Response(status_code=200)
