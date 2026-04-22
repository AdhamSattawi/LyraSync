import uuid
from datetime import datetime
from dataclasses import dataclass
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.infrastructure.ai.audio_transcriber import LLMDataTranscriber
from app.infrastructure.ai.llm_extractor import LLMDataExtractor
from app.domain.schemas.intent_schema import CommandIntent, IntentType
from app.domain.schemas.handler_reply import HandlerReply
from app.infrastructure.database.repositories.conversation_repository import (
    ConversationRepository,
)
from app.infrastructure.ai.vocabulary_loader import load_profession_vocabulary
from app.infrastructure.database.repositories.message_repository import (
    MessageRepository,
)
from app.domain.models.message import Message, MessageDirection
from app.core.intent_handler import IntentHandler
from app.domain.models.user import User


@dataclass
class DispatcherResult:
    """Richer result from process_message for proper logging and auditing."""
    reply: str | HandlerReply
    user_id: uuid.UUID | None = None
    business_id: uuid.UUID | None = None


class AgentDispatcher:
    def __init__(
        self,
        session_maker: AsyncSession,
        transcriber: LLMDataTranscriber,
        extractor: LLMDataExtractor,
        conversation_repository: ConversationRepository,
        handlers: list[IntentHandler],
        message_repository: MessageRepository,
    ):
        self.session_maker = session_maker
        self.transcriber = transcriber
        self.extractor = extractor
        self.conversation_repo = conversation_repository
        self.message_repo = message_repository

        # Build the dynamic registry of installed handlers
        self.registry = {handler.intent_type: handler for handler in handlers}

    async def log_message(
        self,
        from_phone: str,
        to_phone: str,
        content: str | None,
        direction: MessageDirection,
        user_id: uuid.UUID | None = None,
        business_id: uuid.UUID | None = None,
        media_url: str | None = None,
    ):
        async with self.session_maker() as session:
            new_message = Message(
                from_phone=from_phone,
                to_phone=to_phone,
                content=content,
                media_url=media_url,
                direction=direction,
                user_id=user_id,
                business_id=business_id,
            )
            session.add(new_message)
            await session.commit()

    async def process_message(
        self, user_phone: str, message: str | bytes, is_audio: bool
    ) -> DispatcherResult:
        """
        Two-phase session model (fixes BUG-01 spurious ROLLBACK):
        Phase 1: Short-lived dispatcher session — resolve user, transcribe, classify, manage conversation state.
        Phase 2: Handler owns its own session via job_service.session_maker — no session sharing.

        The dispatcher session is cleanly committed and closed before any handler runs.
        """
        handler_call = None  # Holds a coroutine to call after the session closes
        user_id = None
        business_id = None

        # ── Phase 1: All dispatcher work in a short-lived session ────────────
        async with self.session_maker() as session:
            # Step 1: Identify the user and business
            stmt = (
                select(User)
                .options(selectinload(User.business))
                .where(User.phone == user_phone, User.is_active == True)
            )
            user = (await session.execute(stmt)).scalar_one_or_none()
            if not user or not user.business:
                return DispatcherResult(reply="Error: Phone number not registered or no business attached.")

            business = user.business
            
            # ── Subscription Gating [SCALE-01] ────────────────────────────────
            if business.subscription_expires_at and business.subscription_expires_at < datetime.now():
                return DispatcherResult(
                    reply=(
                        f"Your '{business.subscription_plan}' subscription has expired. "
                        "Please visit the dashboard to renew and continue using LyraSync."
                    ),
                    user_id=user.id,
                    business_id=business.id
                )

            business_profession = business.profession.value
            user_id = user.id
            business_id = business.id
            user_language = user.language_preference

            # Step 2: Transcribe audio (if voice note)
            static_vocab = load_profession_vocabulary(business_profession)
            transcript = (
                await self.transcriber.transcribe(
                    message, language=user_language, vocabulary=static_vocab
                )
                if is_audio
                else message
            )

            if not transcript or len(str(transcript).strip()) < 2:
                return DispatcherResult(
                    reply="I'm sorry, I couldn't hear that clearly. Could you please send another voice note or type your request?",
                    user_id=user_id,
                    business_id=business_id,
                )

            # Step 3: Check for an active conversation
            active_state = await self.conversation_repo.get_active(session, user_id)

            if active_state:
                # MID-CONVERSATION: Merge and try to re-extract
                result = await self._continue_conversation(
                    session,
                    user_id,
                    business_id,
                    business_profession,
                    transcript,
                    active_state,
                )
                if callable(result):
                    handler_call = result
                else:
                    # Still incomplete — return clarification prompt
                    return DispatcherResult(reply=result, user_id=user_id, business_id=business_id)
            else:
                # Step 4: Fresh message — classify intent
                system_prompt = (
                    f"You are an AI assistant for a {business_profession} business. "
                    "Classify what the user wants to do based on their message."
                )
                routing_data = await self.extractor.extract(
                    transcript, CommandIntent, system_prompt
                )

                if routing_data.confidence < 0.6:
                    return DispatcherResult(
                        reply=(
                            "I'm not quite sure what you'd like to do. "
                            "Could you please rephrase your request? (e.g., 'Draft a quote for Alice for 500')"
                        ),
                        user_id=user_id,
                        business_id=business_id,
                    )

                # Step 5: Route to the correct handler
                handler = self.registry.get(routing_data.intent)
                if not handler:
                    return DispatcherResult(
                        reply=(
                            f"I'm sorry, I couldn't understand that command or the feature is not yet installed. "
                            f"Intent classified as {routing_data.intent.value}."
                        ),
                        user_id=user_id,
                        business_id=business_id
                    )

                result = await self._extract_and_execute(
                    session,
                    user_id,
                    business_id,
                    business_profession,
                    transcript,
                    routing_data.intent,
                    handler,
                )
                if callable(result):
                    handler_call = result
                else:
                    return DispatcherResult(reply=result, user_id=user_id, business_id=business_id)

        # ── Phase 2: Execute handler AFTER dispatcher session is fully closed ─
        # The dispatcher session committed cleanly and is now closed.
        # The handler opens its own session via job_service.session_maker.
        if handler_call is not None:
            reply = await handler_call()
            return DispatcherResult(reply=reply, user_id=user_id, business_id=business_id)

        return DispatcherResult(reply="I'm having trouble processing that. Please try again.")

    async def _extract_and_execute(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        business_id: uuid.UUID,
        profession: str,
        transcript: str,
        intent: IntentType,
        handler: IntentHandler,
    ):
        """
        Returns either:
        - A string (clarification prompt / error) — dispatcher session stays open.
        - A callable (lambda to execute the handler) — dispatcher session will close first.
        """
        schema = handler.extraction_schema
        if not schema:
            # No schema needed (e.g. LIST_JOBS) — capture handler for Phase 2
            await self.conversation_repo.clear(session, user_id)
            await session.commit()
            return lambda: handler.execute(business_id, user_id, None)

        system_prompt = handler.get_system_prompt(profession)

        try:
            extracted = await self.extractor.extract(transcript, schema, system_prompt)
            # Success — clear conversation state and prepare handler for Phase 2
            await self.conversation_repo.clear(session, user_id)
            await session.commit()
            return lambda: handler.execute(business_id, user_id, extracted)

        except ValidationError as e:
            # Extraction failed — save partial state and return prompt
            missing_fields = self._get_missing_fields(e)
            partial_payload = {"transcript_so_far": transcript}

            await self.conversation_repo.upsert(
                session, user_id, intent.value, partial_payload
            )
            await session.commit()

            return (
                f"I understood you want to {intent.value.replace('_', ' ')}. "
                f"But I still need: {', '.join(missing_fields)}. "
                f"Could you provide that?"
            )

        except Exception:
            return "I am experiencing heavy server load right now. Please try again."

    async def _continue_conversation(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        business_id: uuid.UUID,
        profession: str,
        transcript: str,
        active_state,
    ):
        """
        Returns either a string (still missing fields) or a callable (ready to execute).
        """
        intent = IntentType(active_state.active_intent)
        handler = self.registry.get(intent)

        if not handler:
            await self.conversation_repo.clear(session, user_id)
            await session.commit()
            return "Something went wrong. Let's start over — what would you like to do?"

        previous_transcript = active_state.pending_payload.get("transcript_so_far", "")
        combined_transcript = f"{previous_transcript}\n{transcript}"

        schema = handler.extraction_schema
        if not schema:
            await self.conversation_repo.clear(session, user_id)
            await session.commit()
            return lambda: handler.execute(business_id, user_id, None)

        system_prompt = handler.get_system_prompt(profession)
        system_prompt += "\nThe user is continuing a previous request. Extract required fields from ALL messages combined."

        try:
            extracted = await self.extractor.extract(
                combined_transcript, schema, system_prompt
            )
            await self.conversation_repo.clear(session, user_id)
            await session.commit()
            return lambda: handler.execute(business_id, user_id, extracted)

        except (ValidationError, Exception) as e:
            missing_fields = self._get_missing_fields(e)
            await self.conversation_repo.upsert(
                session,
                user_id,
                intent.value,
                {"transcript_so_far": combined_transcript},
            )
            await session.commit()
            return (
                f"Thanks! I still need: {', '.join(missing_fields)}. "
                f"Could you provide that?"
            )

    @staticmethod
    def _get_missing_fields(error: Exception) -> list[str]:
        """Extract human-readable missing field names from a Pydantic ValidationError."""
        if isinstance(error, ValidationError):
            fields = []
            for err in error.errors():
                loc = err.get("loc", ())
                field_name = " → ".join(str(part) for part in loc) if loc else "unknown"
                fields.append(field_name)
            return fields if fields else ["some required information"]
        return ["some required information"]
