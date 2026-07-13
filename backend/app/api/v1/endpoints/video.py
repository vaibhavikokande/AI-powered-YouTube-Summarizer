from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.video import VideoResponse
from app.services.video_service import VideoService

router = APIRouter(tags=["video"])


@router.get("/video", response_model=VideoResponse)
async def get_video(
    url: str = Query(..., description="A YouTube video, shorts, or youtu.be URL"),
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Validate a YouTube URL and return its metadata, fetching + caching it on first request."""
    service = VideoService(db)
    video = await service.get_or_fetch_video(url)
    return video
