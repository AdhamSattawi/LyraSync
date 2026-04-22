from app.domain.models.client import Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database.repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository[Client]):
    def __init__(self):
        super().__init__(Client)

    async def find_by_name(
        self, business_id, name, session: AsyncSession
    ) -> Client | None:
        stmt = select(Client).where(
            Client.business_id == business_id, Client.name.ilike(name)
        )
        return (await session.execute(stmt)).scalars().first()

    async def find_all_by_business(
        self, business_id, session: AsyncSession
    ) -> list[Client]:
        stmt = select(Client).where(Client.business_id == business_id)
        return (await session.execute(stmt)).scalars().all()
