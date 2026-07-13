from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_provider import LLMProvider
from app.models.enums import QuizQuestionType
from app.models.quiz import Quiz
from app.models.transcript import Transcript
from app.models.video import Video
from app.prompts.quiz_prompts import quiz_prompt
from app.repositories.quiz_repository import QuizRepository
from app.schemas.quiz import QuizGenerationResult
from app.services.content_prep_service import ContentPrepService


class QuizService:
    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider | None = None,
        content_prep: ContentPrepService | None = None,
    ):
        self._repository = QuizRepository(session)
        self._llm = llm_provider or LLMProvider()
        self._content_prep = content_prep or ContentPrepService(session, self._llm)

    async def generate(
        self,
        video: Video,
        transcript: Transcript,
        question_types: list[QuizQuestionType],
        count: int = 10,
    ) -> Quiz:
        existing = await self._repository.get_by_video(video.id)
        if existing is not None:
            return existing

        combined = await self._content_prep.get_combined_summary(transcript)
        result = await self._llm.generate_structured(
            [HumanMessage(content=quiz_prompt(combined, question_types, count))],
            QuizGenerationResult,
        )
        return await self._repository.create(video.id, result.title, result.questions)
