from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_provider import LLMProvider
from app.models.faq import FAQItem
from app.models.transcript import Transcript
from app.models.video import Video
from app.prompts.faq_prompts import faq_prompt
from app.repositories.faq_repository import FAQRepository
from app.schemas.faq import FAQList
from app.services.content_prep_service import ContentPrepService


class FAQService:
    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider | None = None,
        content_prep: ContentPrepService | None = None,
    ):
        self._repository = FAQRepository(session)
        self._llm = llm_provider or LLMProvider()
        self._content_prep = content_prep or ContentPrepService(session, self._llm)

    async def generate(self, video: Video, transcript: Transcript, count: int = 8) -> list[FAQItem]:
        existing = await self._repository.list_by_video(video.id)
        if existing:
            return existing

        combined = await self._content_prep.get_combined_summary(transcript)
        result = await self._llm.generate_structured(
            [HumanMessage(content=faq_prompt(combined, count))], FAQList
        )
        return await self._repository.bulk_create(
            video.id, [(pair.question, pair.answer) for pair in result.items]
        )
