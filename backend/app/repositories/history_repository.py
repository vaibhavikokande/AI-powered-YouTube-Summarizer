import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.history import HistoryEntry
from app.models.video import Video


class HistoryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def touch(self, user_id: uuid.UUID, video_id: uuid.UUID) -> HistoryEntry:
        """Record that a user viewed a video, bumping the timestamp if an
        entry already exists rather than creating a duplicate row.
        """
        result = await self._session.execute(
            select(HistoryEntry).where(
                HistoryEntry.user_id == user_id, HistoryEntry.video_id == video_id
            )
        )
        entry = result.scalar_one_or_none()

        if entry is not None:
            entry.updated_at = datetime.now(timezone.utc)
        else:
            entry = HistoryEntry(user_id=user_id, video_id=video_id)
            self._session.add(entry)

        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def list_by_user(
        self, user_id: uuid.UUID, *, search: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[Video], int]:
        """Recently-viewed videos for a user, optionally filtered by title —
        covers the dashboard's History/Recently-summarized/Search views
        with one query, since they're all the same underlying data.
        """
        stmt = (
            select(Video)
            .join(HistoryEntry, HistoryEntry.video_id == Video.id)
            .where(HistoryEntry.user_id == user_id)
        )
        if search:
            stmt = stmt.where(Video.title.ilike(f"%{search}%"))

        total = (
            await self._session.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        stmt = stmt.order_by(HistoryEntry.updated_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total
