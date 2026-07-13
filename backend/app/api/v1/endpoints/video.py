from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.core.cache import cache_get_json, cache_set_json
from app.db.session import get_db
from app.models.user import User
from app.schemas.video import VideoResponse
from app.services.history_service import HistoryService
from app.services.video_service import VideoService
from app.utils.youtube import extract_video_id

router = APIRouter(tags=["video"])

_VIDEO_CACHE_TTL_SECONDS = 3600


@router.get("/video", response_model=VideoResponse)
async def get_video(
    url: str = Query(..., description="A YouTube video, shorts, or youtu.be URL"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Validate a YouTube URL and return its metadata, fetching + caching it on first request.

    Cached in Redis by video id (1 hour TTL) — a cache tier in front of
    Postgres for the app's highest-traffic read, since a trending video's
    metadata gets requested repeatedly by many different users. Works
    anonymously; if the caller is authenticated, this counts as a view for
    GET /history (videos are globally deduplicated, so history is tracked
    per-user separately from who first created the Video row).
    """
    video_id = extract_video_id(url)
    cache_key = f"video:{video_id}"

    cached = await cache_get_json(cache_key)
    if cached is not None:
        video_response = VideoResponse.model_validate(cached)
    else:
        service = VideoService(db)
        video = await service.get_or_fetch_video(
            url, user_id=current_user.id if current_user else None
        )
        video_response = VideoResponse.model_validate(video)
        await cache_set_json(
            cache_key, video_response.model_dump(mode="json"), _VIDEO_CACHE_TTL_SECONDS
        )

    if current_user is not None:
        await HistoryService(db).record_view(current_user.id, video_response.id)

    return video_response
