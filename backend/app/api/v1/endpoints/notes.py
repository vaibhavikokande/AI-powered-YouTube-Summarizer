from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.note import NoteGenerateRequest, NoteResponse
from app.services.notes_service import NotesService
from app.services.transcript_service import TranscriptService
from app.services.video_service import VideoService

router = APIRouter(tags=["notes"])


@router.post("/notes", response_model=NoteResponse)
async def generate_notes(
    request: NoteGenerateRequest, db: AsyncSession = Depends(get_db)
) -> NoteResponse:
    video = await VideoService(db).get_or_fetch_video(request.url)
    transcript = await TranscriptService(db).get_or_fetch_transcript(
        video_id=video.id, youtube_video_id=video.youtube_video_id
    )
    return await NotesService(db).generate(video, transcript)
