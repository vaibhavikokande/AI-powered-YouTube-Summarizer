import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import QuizQuestionType


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
