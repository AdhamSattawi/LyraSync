from app.domain.models.transaction import Transaction
from app.domain.enums.transaction_type import TransactionType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.infrastructure.database.repositories.base_repository import BaseRepository
import uuid


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self):
        super().__init__(Transaction)

    async def get_balance(
        self, business_id: uuid.UUID, session: AsyncSession
    ) -> dict[str, int]:
        """Calculates total income vs total expense to return rapid net cash flow."""
        stmt = (
            select(Transaction.type, func.sum(Transaction.amount))
            .where(Transaction.business_id == business_id)
            .group_by(Transaction.type)
        )
        results = await session.execute(stmt)
        totals = {TransactionType.INCOME: 0, TransactionType.EXPENSE: 0}

        for row in results:
            totals[row[0]] = row[1] or 0

        totals["net"] = totals[TransactionType.INCOME] - totals[TransactionType.EXPENSE]
        return totals

    async def find_by_business(
        self, business_id: uuid.UUID, session: AsyncSession, limit: int = 50
    ) -> list[Transaction]:
        """Fetch transaction history."""
        stmt = (
            select(Transaction)
            .where(Transaction.business_id == business_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list((await session.execute(stmt)).scalars().all())
