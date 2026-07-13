from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.quiz import QuizGenerateRequest, QuizResponse
from app.services.quiz_service import QuizService
from app.services.transcript_service import TranscriptService
from app.services.video_service import VideoService

router = APIRouter(tags=["quiz"])


@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerateRequest, db: AsyncSession = Depends(get_db)
) -> QuizResponse:
    video = await VideoService(db).get_or_fetch_video(request.url)
    transcript = await TranscriptService(db).get_or_fetch_transcript(
        video_id=video.id, youtube_video_id=video.youtube_video_id
    )
    return await QuizService(db).generate(
        video, transcript, question_types=request.question_types, count=request.count
    )
