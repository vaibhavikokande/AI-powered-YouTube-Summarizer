import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.repositories.history_repository import HistoryRepository


class HistoryService:
    def __init__(self, session: AsyncSession):
        self._repository = HistoryRepository(session)

    async def record_view(self, user_id: uuid.UUID, video_id: uuid.UUID) -> None:
        await self._repository.touch(user_id, video_id)

    async def list_history(
        self, user_id: uuid.UUID, *, search: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[Video], int]:
        return await self._repository.list_by_user(user_id, search=search, limit=limit, offset=offset)
