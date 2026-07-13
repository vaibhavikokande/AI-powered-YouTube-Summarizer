from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.share_link import ShareLinkCreateRequest, ShareLinkResponse
from app.schemas.summary import SummaryResponse
from app.services.share_service import ShareService

router = APIRouter(tags=["share"])


@router.post("/share", response_model=ShareLinkResponse)
async def create_share_link(
    request: ShareLinkCreateRequest, db: AsyncSession = Depends(get_db)
) -> ShareLinkResponse:
    return await ShareService(db).create_share_link(request.summary_id)


@router.get("/share/{token}", response_model=SummaryResponse)
async def get_shared_summary(token: str, db: AsyncSession = Depends(get_db)) -> SummaryResponse:
    """Public endpoint — no auth required, so a shared link works for anyone holding it."""
    return await ShareService(db).resolve_share_link(token)
