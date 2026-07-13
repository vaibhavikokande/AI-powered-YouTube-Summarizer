import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    created_at: datetime


class BookmarkCreate(BaseModel):
    video_id: uuid.UUID
    timestamp_seconds: int
    note: str | None = None


class BookmarkResponse(BookmarkCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
