import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import FAQItem


class FAQRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_video(self, video_id: uuid.UUID) -> list[FAQItem]:
        result = await self._session.execute(select(FAQItem).where(FAQItem.video_id == video_id))
        return list(result.scalars().all())

    async def bulk_create(self, video_id: uuid.UUID, items: list[tuple[str, str]]) -> list[FAQItem]:
        faq_items = [FAQItem(video_id=video_id, question=q, answer=a) for q, a in items]
        self._session.add_all(faq_items)
        await self._session.commit()
        for item in faq_items:
            await self._session.refresh(item)
        return faq_items
