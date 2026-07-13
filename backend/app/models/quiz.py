import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import QuizQuestionType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Quiz(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "quizzes"

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    video: Mapped["Video"] = relationship(back_populates="quizzes")
    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.created_at"
    )


class QuizQuestion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "quiz_questions"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    question_type: Mapped[QuizQuestionType] = mapped_column(
        SAEnum(
            QuizQuestionType,
            name="quiz_question_type",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Populated for MCQ only; null for true/false and fill-in-the-blank.
    options: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
