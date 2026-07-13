import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SummaryType


class TimestampedSection(BaseModel):
    timestamp_seconds: int
    title: str
    summary: str


class TimestampedSectionList(BaseModel):
    """Wraps a list for structured LLM output — providers require a single
    top-level object/schema, not a bare list, for structured/JSON mode.
    """

    sections: list[TimestampedSection]


class KeyTakeaways(BaseModel):
    important_concepts: list[str] = []
    action_items: list[str] = []
    important_quotes: list[str] = []
    definitions: dict[str, str] = {}
    statistics: list[str] = []


class Topics(BaseModel):
    main_topics: list[str] = []
    subtopics: list[str] = []
    tags: list[str] = []


class SummarizeOptions(BaseModel):
    summary_types: list[SummaryType] = [SummaryType.MEDIUM]
    language: str = "en"
    include_mindmap: bool = False


class SummarizeRequest(SummarizeOptions):
    url: str = Field(..., description="A YouTube video, shorts, or youtu.be URL")


class SummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    summary_type: SummaryType
    content: str
    key_takeaways: KeyTakeaways
    timestamped_sections: list[TimestampedSection]
    topics: Topics
    mindmap_markdown: str | None
    llm_provider: str
    created_at: datetime
