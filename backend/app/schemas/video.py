import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SummarizeRequest(BaseModel):
    url: str = Field(..., description="A YouTube video, shorts, or youtu.be URL")


class VideoMetadata(BaseModel):
    """Metadata fetched live from YouTube — not necessarily persisted yet."""

    youtube_video_id: str
    url: str
    title: str | None = None
    description: str | None = None
    channel_name: str | None = None
    channel_id: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    upload_date: str | None = None
    original_language: str | None = None


class VideoResponse(VideoMetadata):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
