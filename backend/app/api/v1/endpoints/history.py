from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.video import VideoResponse
from app.services.history_service import HistoryService

router = APIRouter(tags=["history"])


@router.get("/history", response_model=PaginatedResponse[VideoResponse])
async def get_history(
    search: str | None = Query(None, description="Filter history by video title"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[VideoResponse]:
    """Recently viewed/summarized videos for the current user, optionally searched by title."""
    videos, total = await HistoryService(db).list_history(
        current_user.id, search=search, limit=limit, offset=offset
    )
    return PaginatedResponse(items=videos, total=total, limit=limit, offset=offset)
