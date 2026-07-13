from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.transcript import TranscriptResponse
from app.services.transcript_service import TranscriptService
from app.services.video_service import VideoService

router = APIRouter(tags=["transcript"])


@router.get("/transcript", response_model=TranscriptResponse)
async def get_transcript(
    url: str = Query(..., description="A YouTube video, shorts, or youtu.be URL"),
    language: str = Query(
        "en", description="Preferred transcript language code; falls back automatically"
    ),
    translate_to_english: bool = Query(
        True, description="Translate to English if the source transcript isn't English"
    ),
    db: AsyncSession = Depends(get_db),
) -> TranscriptResponse:
    """Validate the URL, resolve (or create) the video, and return its transcript."""
    video = await VideoService(db).get_or_fetch_video(url)
    transcript = await TranscriptService(db).get_or_fetch_transcript(
        video_id=video.id,
        youtube_video_id=video.youtube_video_id,
        preferred_language=language,
        translate_to_english=translate_to_english,
    )
    return transcript
