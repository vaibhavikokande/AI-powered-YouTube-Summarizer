import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SummaryType
from app.models.summary import Summary


class SummaryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_video_and_type(
        self, video_id: uuid.UUID, summary_type: SummaryType
    ) -> Summary | None:
        result = await self._session.execute(
            select(Summary).where(
                Summary.video_id == video_id, Summary.summary_type == summary_type
            )
        )
        return result.scalar_one_or_none()

    async def list_by_video(self, video_id: uuid.UUID) -> list[Summary]:
        result = await self._session.execute(select(Summary).where(Summary.video_id == video_id))
        return list(result.scalars().all())

    async def create(
        self,
        *,
        video_id: uuid.UUID,
        user_id: uuid.UUID | None,
        summary_type: SummaryType,
        content: str,
        key_takeaways: dict,
        timestamped_sections: list[dict],
        topics: dict,
        llm_provider: str,
        mindmap_markdown: str | None = None,
    ) -> Summary:
        summary = Summary(
            video_id=video_id,
            user_id=user_id,
            summary_type=summary_type,
            content=content,
            key_takeaways=key_takeaways,
            timestamped_sections=timestamped_sections,
            topics=topics,
            mindmap_markdown=mindmap_markdown,
            llm_provider=llm_provider,
        )
        self._session.add(summary)
        await self._session.commit()
        await self._session.refresh(summary)
        return summary
