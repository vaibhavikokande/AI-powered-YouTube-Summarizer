import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.favorite import BookmarkCreate, BookmarkResponse
from app.services.bookmark_service import BookmarkService

router = APIRouter(tags=["bookmarks"])


@router.get("/bookmarks", response_model=list[BookmarkResponse])
async def list_bookmarks(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[BookmarkResponse]:
    return await BookmarkService(db).list_bookmarks(current_user.id)


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def add_bookmark(
    request: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookmarkResponse:
    return await BookmarkService(db).add_bookmark(current_user.id, request)


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(
    bookmark_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await BookmarkService(db).remove_bookmark(current_user.id, bookmark_id)
