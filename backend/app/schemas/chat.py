import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ChatRole


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: ChatRole
    content: str
    created_at: datetime


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    created_at: datetime
    messages: list[ChatMessageResponse] = []
