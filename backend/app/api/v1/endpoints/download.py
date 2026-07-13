import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.repositories.summary_repository import SummaryRepository
from app.repositories.video_repository import VideoRepository
from app.services.export_service import ExportService

router = APIRouter(tags=["download"])


@router.get("/download")
async def download_summary(
    summary_id: uuid.UUID = Query(...),
    export_format: str = Query(
        ..., alias="format", pattern="^(pdf|docx|markdown|txt)$", description="pdf, docx, markdown, or txt"
    ),
    db: AsyncSession = Depends(get_db),
) -> Response:
    summary = await SummaryRepository(db).get_by_id(summary_id)
    if summary is None:
        raise NotFoundError(f"Summary {summary_id} not found.")

    video = await VideoRepository(db).get_by_id(summary.video_id)

    exported = ExportService().export(summary, video.title if video else None, export_format)

    return Response(
        content=exported.content,
        media_type=exported.media_type,
        headers={"Content-Disposition": f'attachment; filename="{exported.filename}"'},
    )
