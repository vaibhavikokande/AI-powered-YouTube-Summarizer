import uuid

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Favorite(Base, UUIDPKMixin, TimestampMixin):
    """A user favoriting an entire video (surfaced on the dashboard)."""

    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "video_id", name="uq_favorites_user_video"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user: Mapped["User"] = relationship(back_populates="favorites")
    video: Mapped["Video"] = relationship(back_populates="favorited_by")


class Bookmark(Base, UUIDPKMixin, TimestampMixin):
    """A saved timestamp within a video — distinct from favoriting the whole video."""

    __tablename__ = "bookmarks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="bookmarks")
    video: Mapped["Video"] = relationship(back_populates="bookmarks")
