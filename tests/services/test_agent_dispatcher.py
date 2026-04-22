import pytest
import uuid
from app.services.agent_dispatcher import AgentDispatcher
from unittest.mock import AsyncMock, MagicMock
from app.domain.schemas.intent_schema import IntentType, CommandIntent
from pydantic import BaseModel, Field, ValidationError

# --- Dummy Schemas for Testing --- #
class DummyCommandSchema(BaseModel):
    amount: int = Field(...)
    client_name: str = Field(...)

# --- Fixtures --- #
@pytest.fixture
def session_maker() -> AsyncMock:
    session_mock = AsyncMock()
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session_mock
    return MagicMock(return_value=session_context)

@pytest.fixture
def transcriber() -> AsyncMock:
    return AsyncMock()

@pytest.fixture
def extractor() -> AsyncMock:
    return AsyncMock()

@pytest.fixture
def conversation_repository() -> AsyncMock:
    return AsyncMock()

@pytest.fixture
def message_repository() -> AsyncMock:
    return AsyncMock()

@pytest.fixture
def handlers():
    handler = MagicMock()
    handler.intent_type = IntentType.DRAFT_QUOTE
    handler.extraction_schema = DummyCommandSchema
    # Mock synchronous get_system_prompt
    handler.get_system_prompt = MagicMock(return_value="You are an AI assistant for a business.")
    handler.execute = AsyncMock(return_value="Quote drafted successfully.")
    return [handler]

@pytest.fixture
def dispatcher(session_maker, transcriber, extractor, conversation_repository, message_repository, handlers):
    return AgentDispatcher(
        session_maker=session_maker,
        transcriber=transcriber,
        extractor=extractor,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        handlers=handlers
    )

# --- Tests --- #

@pytest.mark.asyncio
async def test_dispatcher_handles_validation_error(
    dispatcher, extractor, conversation_repository, session_maker, handlers
):
    """
    Phase 2: Output Parsing (Hallucination)
    Asserts a Pydantic ValidationError caused by missing fields triggers safe 
    ConversationState storage, rather than an exception crash.
    """
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    audio_path = "fake.ogg"

    # 1. Setup mock intent recognizing our handler
    command_intent = CommandIntent(
        reasoning="Testing", confidence=0.99, intent=IntentType.DRAFT_QUOTE
    )
    dispatcher._extract_intent = AsyncMock(return_value=command_intent)

    # 2. Setup Transcriber to return a string
    dispatcher.transcriber.transcribe_audio = AsyncMock(return_value="I want to draft a quote")

    # 3. Force extractor to raise ValidationError (simulate missing 'amount')
    error_mock = ValidationError.from_exception_data("DummyCommandSchema", [{"type": "missing", "loc": ("amount",), "input": {}}])
    extractor.extract.side_effect = error_mock

    # 4. Execute
    response = await dispatcher._extract_and_execute(
        session=AsyncMock(),
        user_id=user_id,
        business_id=business_id,
        profession="profession",
        transcript="I want to draft a quote",
        intent=IntentType.DRAFT_QUOTE,
        handler=handlers[0]
    )

    # 5. Assertions
    # Ensure it did not crash, but returned partial state response
    assert "But I still need" in response
    assert "amount" in response

    # Assert the conversation state was safely UPSERTED to PostgreSQL so it remembers this
    # Assert the conversation state was safely UPSERTED to PostgreSQL so it remembers this
    conversation_repository.upsert.assert_awaited_once()
    assert conversation_repository.upsert.call_args[0][2] == IntentType.DRAFT_QUOTE.value
    assert conversation_repository.upsert.call_args[0][3]['transcript_so_far'] == "I want to draft a quote"


@pytest.mark.asyncio
async def test_continue_conversation_merges_transcript(
    dispatcher, extractor, conversation_repository, session_maker
):
    """
    Phase 3: Memory and Context Management
    Asserts that if the database holds prior context, the Dispather concatenates 
    the new prompt seamlessly before sending it to the LLM.
    """
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # 1. Mock the repository returning an active state (user forgot 'amount' previously)
    active_state = MagicMock()
    active_state.active_intent = IntentType.DRAFT_QUOTE.value
    active_state.pending_payload = {"transcript_so_far": "I want to draft a quote for Alice."}
    conversation_repository.get_active = AsyncMock(return_value=active_state)

    dispatcher.transcriber.transcribe_audio = AsyncMock(return_value="The amount is 500.")

    # 2. Mock extractor to SUCCESS this time.
    extractor.extract.side_effect = None
    extractor.extract.return_value = DummyCommandSchema(amount=500, client_name="Alice")

    # 3. Execute _continue_conversation
    handler_call = await dispatcher._continue_conversation(
        session=AsyncMock(),
        user_id=user_id,
        business_id=business_id,
        profession="profession",
        transcript="The amount is 500.",
        active_state=active_state
    )

    # 4. Assertions
    # Since _continue_conversation returns a callable (Phase 2), execute it
    result = await handler_call()
    assert result == "Quote drafted successfully."
    
    # Verify the text sent to the LLM extractor was correctly COMBINED
    extracted_text_sent_to_model = extractor.extract.call_args[0][0]
    assert "I want to draft a quote for Alice." in extracted_text_sent_to_model
    assert "The amount is 500." in extracted_text_sent_to_model

    # Verify conversation memory is cleared via clear
    conversation_repository.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispatcher_handles_server_timeout(
    dispatcher, extractor, conversation_repository, handlers
):
    """
    Phase 4: Resilience & API Timeout
    Asserts that if OpenAI completely crashes/times out, the webhook safely returns 
    a fallback string and avoids dropping dirty state into the database.
    """
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # Force a generic Exception representing API timeout
    extractor.extract.side_effect = TimeoutError("OpenAI API timed out.")

    response = await dispatcher._extract_and_execute(
        session=AsyncMock(),
        user_id=user_id,
        business_id=business_id,
        profession="profession",
        transcript="I want to draft a quote",
        intent=IntentType.DRAFT_QUOTE,
        handler=handlers[0]
    )

    # Assert fallback string is returned exactly as coded
    assert "heavy server load right now" in response

    # Crucial: Assert that Upsert was NEVER called. (Do not save broken API state)
    conversation_repository.upsert.assert_not_called()
