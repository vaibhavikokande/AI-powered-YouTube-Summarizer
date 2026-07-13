from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.flashcard import FlashcardGenerateRequest, FlashcardResponse
from app.services.flashcard_service import FlashcardService
from app.services.transcript_service import TranscriptService
from app.services.video_service import VideoService

router = APIRouter(tags=["flashcards"])


@router.post("/flashcards", response_model=list[FlashcardResponse])
async def generate_flashcards(
    request: FlashcardGenerateRequest, db: AsyncSession = Depends(get_db)
) -> list[FlashcardResponse]:
    video = await VideoService(db).get_or_fetch_video(request.url)
    transcript = await TranscriptService(db).get_or_fetch_transcript(
        video_id=video.id, youtube_video_id=video.youtube_video_id
    )
    return await FlashcardService(db).generate(video, transcript, count=request.count)
