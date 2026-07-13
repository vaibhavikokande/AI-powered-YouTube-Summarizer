import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.repositories.summary_repository import SummaryRepository
from app.services.tts_service import TTSService

router = APIRouter(tags=["tts"])


@router.get("/tts")
async def get_voice_summary(
    summary_id: uuid.UUID = Query(...), db: AsyncSession = Depends(get_db)
) -> Response:
    """Generates a spoken-word MP3 of a summary's content on demand."""
    summary = await SummaryRepository(db).get_by_id(summary_id)
    if summary is None:
        raise NotFoundError(f"Summary {summary_id} not found.")

    audio = await TTSService().generate_audio(summary.content)
    return Response(content=audio, media_type="audio/mpeg")
