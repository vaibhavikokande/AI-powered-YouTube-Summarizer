import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class ShareLink(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "share_links"

    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("summaries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    summary: Mapped["Summary"] = relationship(back_populates="share_links")
