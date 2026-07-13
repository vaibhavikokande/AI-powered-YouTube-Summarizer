import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    content_markdown: str
    created_at: datetime
