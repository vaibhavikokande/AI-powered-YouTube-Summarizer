import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.favorite import Bookmark
from app.repositories.bookmark_repository import BookmarkRepository
from app.schemas.favorite import BookmarkCreate


class BookmarkService:
    def __init__(self, session: AsyncSession):
        self._repository = BookmarkRepository(session)

    async def list_bookmarks(self, user_id: uuid.UUID) -> list[Bookmark]:
        return await self._repository.list_by_user(user_id)

    async def add_bookmark(self, user_id: uuid.UUID, data: BookmarkCreate) -> Bookmark:
        return await self._repository.create(
            user_id, data.video_id, data.timestamp_seconds, data.note
        )

    async def remove_bookmark(self, user_id: uuid.UUID, bookmark_id: uuid.UUID) -> None:
        bookmark = await self._repository.get(bookmark_id)
        if bookmark is None:
            raise NotFoundError("Bookmark not found.")
        if bookmark.user_id != user_id:
            raise ForbiddenError("You do not have access to this bookmark.")
        await self._repository.delete(bookmark)
