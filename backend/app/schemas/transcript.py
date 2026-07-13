import uuid

from pydantic import BaseModel, ConfigDict


class TranscriptSegment(BaseModel):
    start: float
    duration: float
    text: str


class TranscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    language: str
    is_auto_generated: bool
    is_translated: bool
    source_language: str | None
    full_text: str
    segments: list[TranscriptSegment]
