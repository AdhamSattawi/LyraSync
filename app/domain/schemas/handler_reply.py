from pydantic import BaseModel


class HandlerReply(BaseModel):
    """
    Minimal structured reply from an IntentHandler.

    Used when a handler needs to return more than plain text — specifically
    when a media file (PDF, image) should accompany the message.

    The dispatcher passes this through to the messaging adapter, which maps
    `media_url` to the platform's media delivery mechanism (e.g., Twilio's
    `media_url` parameter for WhatsApp, or an email attachment URL).

    Future upgrade path: When [ARCH-01] AI Orchestration Layer is built,
    this is replaced by the full `AgentReply` schema from `agent_reply.py`.
    """

    text: str
    media_url: str | None = None
