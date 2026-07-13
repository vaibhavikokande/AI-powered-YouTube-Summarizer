import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz, QuizQuestion
from app.schemas.quiz import QuizQuestionPair


class QuizRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_video(self, video_id: uuid.UUID) -> Quiz | None:
        result = await self._session.execute(
            select(Quiz).where(Quiz.video_id == video_id).options(selectinload(Quiz.questions))
        )
        return result.scalar_one_or_none()

    async def create(
        self, video_id: uuid.UUID, title: str, questions: list[QuizQuestionPair]
    ) -> Quiz:
        quiz = Quiz(
            video_id=video_id,
            title=title,
            questions=[
                QuizQuestion(
                    question_type=q.question_type,
                    question_text=q.question_text,
                    options=q.options,
                    correct_answer=q.correct_answer,
                    explanation=q.explanation,
                )
                for q in questions
            ],
        )
        self._session.add(quiz)
        await self._session.commit()
        await self._session.refresh(quiz, attribute_names=["questions"])
        return quiz
