import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.favorite import FavoriteResponse
from app.services.favorite_service import FavoriteService

router = APIRouter(tags=["favorites"])


@router.get("/favorites", response_model=list[FavoriteResponse])
async def list_favorites(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[FavoriteResponse]:
    return await FavoriteService(db).list_favorites(current_user.id)


@router.post(
    "/favorites/{video_id}", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED
)
async def add_favorite(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FavoriteResponse:
    return await FavoriteService(db).add_favorite(current_user.id, video_id)


@router.delete("/favorites/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await FavoriteService(db).remove_favorite(current_user.id, video_id)
