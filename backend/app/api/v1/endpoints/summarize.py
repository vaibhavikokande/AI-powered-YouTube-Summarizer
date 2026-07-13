from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.summary import SummarizeRequest, SummaryResponse
from app.services.summarization_service import SummarizationService
from app.services.transcript_service import TranscriptService
from app.services.video_service import VideoService

router = APIRouter(tags=["summarize"])


@router.post("/summarize", response_model=list[SummaryResponse])
async def summarize_video(
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
) -> list[SummaryResponse]:
    """Validate the URL, resolve video + transcript, and return the requested summaries.

    Runs synchronously today (as do /video and /transcript). Step 11 moves
    this behind a Celery job once multi-hour transcripts make the request
    latency here worth backgrounding, per docs/SPEC.md's API standards.
    """
    video = await VideoService(db).get_or_fetch_video(request.url)
    transcript = await TranscriptService(db).get_or_fetch_transcript(
        video_id=video.id,
        youtube_video_id=video.youtube_video_id,
        preferred_language=request.language,
    )
    summaries = await SummarizationService(db).summarize(
        video=video, transcript=transcript, summary_types=request.summary_types
    )
    return summaries
