import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Video(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "videos"

    youtube_video_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)

    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Stored as the ISO date string YouTube returns rather than a Date column,
    # since some sources only provide partial/relative dates.
    upload_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    original_language: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_by: Mapped["User"] = relationship(back_populates="videos")
    transcripts: Mapped[list["Transcript"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    summaries: Mapped[list["Summary"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    flashcards: Mapped[list["Flashcard"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    faq_items: Mapped[list["FAQItem"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    favorited_by: Mapped[list["Favorite"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
