from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.schemas.transaction_schema import TransactionExtract, TransactionSchema
from app.domain.models.transaction import Transaction
import uuid
from app.infrastructure.database.repositories.transaction_repository import (
    TransactionRepository,
)
from app.infrastructure.database.repositories.business_repository import (
    BusinessRepository,
)


class TransactionService:
    def __init__(
        self,
        session_maker: AsyncSession,
        transaction_repository: TransactionRepository,
        business_repository: BusinessRepository,
    ):
        self.session_maker = session_maker
        self.transaction_repo = transaction_repository
        self.business_repo = business_repository

    async def log_transaction(
        self, business_id: uuid.UUID, user_id: uuid.UUID, data: TransactionExtract
    ) -> TransactionSchema:
        async with self.session_maker() as session:
            currency_code = await self.business_repo.get_currency_code(
                business_id, session
            )

            new_transaction = Transaction(
                business_id=business_id,
                user_id=user_id,
                type=data.type,
                amount=data.amount,
                currency_code=currency_code,
                category=data.category,
                description=data.description,
                status=data.status,
            )

            await self.transaction_repo.save(new_transaction, session)
            await session.commit()
            await session.refresh(new_transaction)

            return TransactionSchema.model_validate(new_transaction)

    async def get_cash_flow(
        self, business_id: uuid.UUID, user_id: uuid.UUID, data: None = None
    ) -> str:
        """Returns a string summary of the cash flow."""
        async with self.session_maker() as session:
            totals = await self.transaction_repo.get_balance(business_id, session)
            currency_code = await self.business_repo.get_currency_code(
                business_id, session
            )

            income = totals["income"] / 100
            expense = totals["expense"] / 100
            net = totals["net"] / 100

            return (
                f"Here is your Cash Flow Summary:\n"
                f"Gross Income: {income:,.2f} {currency_code}\n"
                f"Total Expenses: {expense:,.2f} {currency_code}\n"
                f"Net Cash Flow: {net:,.2f} {currency_code}"
            )
