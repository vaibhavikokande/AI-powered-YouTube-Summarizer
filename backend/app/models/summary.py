import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SummaryType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Summary(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "summaries"

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    summary_type: Mapped[SummaryType] = mapped_column(
        SAEnum(
            SummaryType,
            name="summary_type",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured extras stored as JSONB — see schemas.summary for the shape
    # (important_concepts, action_items, important_quotes, definitions, statistics).
    key_takeaways: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # List of {timestamp_seconds, title, summary}.
    timestamped_sections: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    # {main_topics: [...], subtopics: [...], tags: [...]}.
    topics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    mindmap_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    llm_provider: Mapped[str] = mapped_column(String(32), nullable=False)

    video: Mapped["Video"] = relationship(back_populates="summaries")
    share_links: Mapped[list["ShareLink"]] = relationship(
        back_populates="summary", cascade="all, delete-orphan"
    )
