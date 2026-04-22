from typing import TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository pattern. Repositories NEVER commit — the service layer
    owns the transaction boundary via `async with session_maker() as session`.
    """

    def __init__(self, model: Type[T]):
        self.model = model

    async def save(self, entity: T, session: AsyncSession) -> T:
        session.add(entity)
        await session.flush()
        return entity

    async def delete(self, entity: T, session: AsyncSession) -> None:
        await session.delete(entity)

    async def find_by_id(self, entity_id: uuid.UUID, session: AsyncSession) -> T | None:
        stmt = select(self.model).where(self.model.id == entity_id)
        return (await session.execute(stmt)).scalars().first()

    async def find_all(self, session: AsyncSession) -> list[T]:
        stmt = select(self.model)
        return (await session.execute(stmt)).scalars().all()

    async def find_by_business_id(
        self, business_id: uuid.UUID, session: AsyncSession
    ) -> list[T]:
        stmt = select(self.model).where(self.model.business_id == business_id)
        return (await session.execute(stmt)).scalars().all()
