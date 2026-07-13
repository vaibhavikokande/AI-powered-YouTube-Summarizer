import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note


class NoteRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_video(self, video_id: uuid.UUID) -> Note | None:
        result = await self._session.execute(select(Note).where(Note.video_id == video_id))
        return result.scalar_one_or_none()

    async def create(
        self, video_id: uuid.UUID, content_markdown: str, user_id: uuid.UUID | None = None
    ) -> Note:
        note = Note(video_id=video_id, user_id=user_id, content_markdown=content_markdown)
        self._session.add(note)
        await self._session.commit()
        await self._session.refresh(note)
        return note
