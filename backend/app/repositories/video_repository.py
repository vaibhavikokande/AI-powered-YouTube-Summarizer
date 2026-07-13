import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.schemas.video import VideoMetadata


class VideoRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_youtube_id(self, youtube_video_id: str) -> Video | None:
        result = await self._session.execute(
            select(Video).where(Video.youtube_video_id == youtube_video_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, metadata: VideoMetadata, created_by_user_id: uuid.UUID | None = None
    ) -> Video:
        video = Video(
            youtube_video_id=metadata.youtube_video_id,
            url=metadata.url,
            title=metadata.title,
            description=metadata.description,
            channel_name=metadata.channel_name,
            channel_id=metadata.channel_id,
            thumbnail_url=metadata.thumbnail_url,
            duration_seconds=metadata.duration_seconds,
            view_count=metadata.view_count,
            upload_date=metadata.upload_date,
            original_language=metadata.original_language,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(video)
        await self._session.commit()
        await self._session.refresh(video)
        return video
