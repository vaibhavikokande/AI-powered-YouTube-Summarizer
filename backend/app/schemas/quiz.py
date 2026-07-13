import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import QuizQuestionType


class QuizGenerateRequest(BaseModel):
    url: str = Field(..., description="A YouTube video, shorts, or youtu.be URL")
    question_types: list[QuizQuestionType] = [
        QuizQuestionType.MCQ,
        QuizQuestionType.TRUE_FALSE,
        QuizQuestionType.FILL_BLANK,
    ]
    count: int = Field(default=10, ge=1, le=30)


class QuizQuestionPair(BaseModel):
    question_type: QuizQuestionType
    question_text: str
    options: list[str] | None = None
    correct_answer: str
    explanation: str | None = None


class QuizGenerationResult(BaseModel):
    """Wraps the generated quiz for structured LLM output."""

    title: str
    questions: list[QuizQuestionPair]


class QuizQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_type: QuizQuestionType
    question_text: str
    options: list[str] | None
    correct_answer: str
    explanation: str | None


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    questions: list[QuizQuestionResponse]
