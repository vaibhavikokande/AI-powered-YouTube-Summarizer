import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class HistoryEntry(Base, UUIDPKMixin, TimestampMixin):
    """Tracks that a user has viewed/summarized a video, independent of who
    first created the (globally deduplicated) `Video` row.

    `Video` is shared across all users — the first person to summarize a
    given YouTube URL creates the one `Video` row everyone else reuses. A
    single `created_by_user_id` on `Video` can't represent "this is in my
    history" for every user who's looked at it, so history is tracked here
    instead, with `updated_at` (via TimestampMixin) doubling as "last viewed".
    """

    __tablename__ = "history_entries"
    __table_args__ = (UniqueConstraint("user_id", "video_id", name="uq_history_entries_user_video"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user: Mapped["User"] = relationship(back_populates="history_entries")
    video: Mapped["Video"] = relationship(back_populates="history_entries")
