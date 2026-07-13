from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.faq import FAQGenerateRequest, FAQItemResponse
from app.services.faq_service import FAQService
from app.services.transcript_service import TranscriptService
from app.services.video_service import VideoService

router = APIRouter(tags=["faq"])


@router.post("/faq", response_model=list[FAQItemResponse])
async def generate_faq(
    request: FAQGenerateRequest, db: AsyncSession = Depends(get_db)
) -> list[FAQItemResponse]:
    video = await VideoService(db).get_or_fetch_video(request.url)
    transcript = await TranscriptService(db).get_or_fetch_transcript(
        video_id=video.id, youtube_video_id=video.youtube_video_id
    )
    return await FAQService(db).generate(video, transcript, count=request.count)
