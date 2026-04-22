from app.core.intent_handler import IntentHandler
from app.domain.schemas.intent_schema import IntentType
from app.services.transaction_service import TransactionService
import uuid


class CheckBalanceHandler(IntentHandler):
    def __init__(self, transaction_service: TransactionService):
        self.transaction_service = transaction_service

    @property
    def intent_type(self) -> IntentType:
        return IntentType.CHECK_BALANCE

    @property
    def extraction_schema(self):
        return None  # Just executing a query, no LLM schema extraction needed.

    def get_system_prompt(self, profession: str) -> str:
        return ""

    async def execute(
        self, business_id: uuid.UUID, user_id: uuid.UUID, extracted_data: None = None
    ) -> str:
        return await self.transaction_service.get_cash_flow(business_id, user_id)
