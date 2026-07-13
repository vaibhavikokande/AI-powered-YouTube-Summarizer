import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flashcard import Flashcard


class FlashcardRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_video(self, video_id: uuid.UUID) -> list[Flashcard]:
        result = await self._session.execute(
            select(Flashcard).where(Flashcard.video_id == video_id)
        )
        return list(result.scalars().all())

    async def bulk_create(
        self, video_id: uuid.UUID, items: list[tuple[str, str]]
    ) -> list[Flashcard]:
        flashcards = [Flashcard(video_id=video_id, question=q, answer=a) for q, a in items]
        self._session.add_all(flashcards)
        await self._session.commit()
        for card in flashcards:
            await self._session.refresh(card)
        return flashcards
