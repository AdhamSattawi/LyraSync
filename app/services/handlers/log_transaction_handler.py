from app.core.intent_handler import IntentHandler
from app.domain.schemas.intent_schema import IntentType
from app.domain.schemas.transaction_schema import TransactionExtract
from app.services.transaction_service import TransactionService
from app.domain.enums.transaction_type import TransactionType as TType
import uuid


class LogTransactionHandler(IntentHandler):
    """Handles both LOG_INCOME and LOG_EXPENSE by passing the correct intent_type."""

    def __init__(
        self, transaction_service: TransactionService, intent_type: IntentType
    ):
        self.transaction_service = transaction_service
        self._intent_type = intent_type

    @property
    def intent_type(self) -> IntentType:
        return self._intent_type

    @property
    def extraction_schema(self):
        return TransactionExtract

    def get_system_prompt(self, profession: str) -> str:
        ttype = "INCOME" if self._intent_type == IntentType.LOG_INCOME else "EXPENSE"
        return (
            f"You are an AI assistant for a {profession} business. "
            f"The user wants to log an {ttype}. "
            "Extract the exact transaction amount, a short category, and a description. "
            f"Ensure the 'type' field is set to '{ttype.lower()}'. "
            "Return the data in the TransactionExtract schema. Make sure amount is in minor units (e.g. cents/pence)."
        )

    async def execute(
        self,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        extracted_data: TransactionExtract,
    ) -> str:
        # Enforce type match from the intent router just in case the LLM messes up
        extracted_data.type = (
            TType.INCOME
            if self._intent_type == IntentType.LOG_INCOME
            else TType.EXPENSE
        )

        transaction = await self.transaction_service.log_transaction(
            business_id, user_id, extracted_data
        )

        t_type_str = "Income" if transaction.type == TType.INCOME else "Expense"
        return f"Logged {t_type_str.lower()} of {transaction.amount / 100:.2f} {transaction.currency_code} for {transaction.category}."
