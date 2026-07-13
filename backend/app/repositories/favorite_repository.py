import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Favorite


class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_user(self, user_id: uuid.UUID) -> list[Favorite]:
        result = await self._session.execute(
            select(Favorite).where(Favorite.user_id == user_id).order_by(Favorite.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, user_id: uuid.UUID, video_id: uuid.UUID) -> Favorite | None:
        result = await self._session.execute(
            select(Favorite).where(Favorite.user_id == user_id, Favorite.video_id == video_id)
        )
        return result.scalar_one_or_none()

    async def add(self, user_id: uuid.UUID, video_id: uuid.UUID) -> Favorite:
        favorite = Favorite(user_id=user_id, video_id=video_id)
        self._session.add(favorite)
        await self._session.commit()
        await self._session.refresh(favorite)
        return favorite

    async def remove(self, favorite: Favorite) -> None:
        await self._session.delete(favorite)
        await self._session.commit()
