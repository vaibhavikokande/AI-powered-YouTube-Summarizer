from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.schemas.video import VideoResponse
from app.services.history_service import HistoryService
from app.services.video_service import VideoService

router = APIRouter(tags=["video"])


@router.get("/video", response_model=VideoResponse)
async def get_video(
    url: str = Query(..., description="A YouTube video, shorts, or youtu.be URL"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Validate a YouTube URL and return its metadata, fetching + caching it on first request.

    Works anonymously; if the caller is authenticated, this counts as a
    view for GET /history (videos are globally deduplicated, so history is
    tracked per-user separately from who first created the Video row).
    """
    service = VideoService(db)
    video = await service.get_or_fetch_video(url, user_id=current_user.id if current_user else None)

    if current_user is not None:
        await HistoryService(db).record_view(current_user.id, video.id)

    return video
