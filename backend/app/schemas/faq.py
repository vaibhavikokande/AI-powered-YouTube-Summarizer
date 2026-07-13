import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FAQGenerateRequest(BaseModel):
    url: str = Field(..., description="A YouTube video, shorts, or youtu.be URL")
    count: int = Field(default=8, ge=1, le=20)


class FAQPair(BaseModel):
    question: str
    answer: str


class FAQList(BaseModel):
    """Wraps a list for structured LLM output."""

    items: list[FAQPair]


class FAQItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    answer: str
    created_at: datetime
