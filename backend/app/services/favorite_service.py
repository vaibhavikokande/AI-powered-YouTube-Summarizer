import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.favorite import Favorite
from app.repositories.favorite_repository import FavoriteRepository


class FavoriteService:
    def __init__(self, session: AsyncSession):
        self._repository = FavoriteRepository(session)

    async def list_favorites(self, user_id: uuid.UUID) -> list[Favorite]:
        return await self._repository.list_by_user(user_id)

    async def add_favorite(self, user_id: uuid.UUID, video_id: uuid.UUID) -> Favorite:
        existing = await self._repository.get(user_id, video_id)
        if existing is not None:
            return existing
        return await self._repository.add(user_id, video_id)

    async def remove_favorite(self, user_id: uuid.UUID, video_id: uuid.UUID) -> None:
        existing = await self._repository.get(user_id, video_id)
        if existing is None:
            raise NotFoundError("Favorite not found.")
        await self._repository.remove(existing)
