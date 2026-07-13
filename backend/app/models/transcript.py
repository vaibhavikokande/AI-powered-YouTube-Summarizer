import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Transcript(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "transcripts"

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    language: Mapped[str] = mapped_column(String(16), nullable=False)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_translated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_language: Mapped[str | None] = mapped_column(String(16), nullable=True)

    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    # List of {start, duration, text} segments as returned by the transcript API.
    segments: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    video: Mapped["Video"] = relationship(back_populates="transcripts")
