import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Bookmark


class BookmarkRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_user(self, user_id: uuid.UUID) -> list[Bookmark]:
        result = await self._session.execute(
            select(Bookmark).where(Bookmark.user_id == user_id).order_by(Bookmark.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, bookmark_id: uuid.UUID) -> Bookmark | None:
        return await self._session.get(Bookmark, bookmark_id)

    async def create(
        self, user_id: uuid.UUID, video_id: uuid.UUID, timestamp_seconds: int, note: str | None
    ) -> Bookmark:
        bookmark = Bookmark(
            user_id=user_id, video_id=video_id, timestamp_seconds=timestamp_seconds, note=note
        )
        self._session.add(bookmark)
        await self._session.commit()
        await self._session.refresh(bookmark)
        return bookmark

    async def delete(self, bookmark: Bookmark) -> None:
        await self._session.delete(bookmark)
        await self._session.commit()
