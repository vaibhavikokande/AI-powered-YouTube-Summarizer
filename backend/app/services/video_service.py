import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.repositories.video_repository import VideoRepository
from app.services.metadata_service import MetadataService
from app.utils.youtube import extract_video_id


class VideoService:
    def __init__(self, session: AsyncSession):
        self._repository = VideoRepository(session)
        self._metadata_service = MetadataService()

    async def get_or_fetch_video(self, url: str, user_id: uuid.UUID | None = None) -> Video:
        """Return the existing Video row for this URL, or fetch + persist it.

        Videos are deduplicated by youtube_video_id: summarizing the same
        URL twice reuses the stored metadata instead of hitting YouTube again.
        """
        video_id = extract_video_id(url)

        existing = await self._repository.get_by_youtube_id(video_id)
        if existing is not None:
            return existing

        metadata = await self._metadata_service.fetch_metadata(url)
        return await self._repository.create(metadata, created_by_user_id=user_id)
