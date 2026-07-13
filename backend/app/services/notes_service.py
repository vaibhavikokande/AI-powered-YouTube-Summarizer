from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_provider import LLMProvider
from app.models.note import Note
from app.models.transcript import Transcript
from app.models.video import Video
from app.prompts.notes_prompts import notes_prompt
from app.repositories.note_repository import NoteRepository
from app.services.content_prep_service import ContentPrepService


class NotesService:
    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider | None = None,
        content_prep: ContentPrepService | None = None,
    ):
        self._repository = NoteRepository(session)
        self._llm = llm_provider or LLMProvider()
        self._content_prep = content_prep or ContentPrepService(session, self._llm)

    async def generate(self, video: Video, transcript: Transcript) -> Note:
        existing = await self._repository.get_by_video(video.id)
        if existing is not None:
            return existing

        combined = await self._content_prep.get_combined_summary(transcript)
        content_markdown = await self._llm.generate_text(
            [HumanMessage(content=notes_prompt(combined, video.title))]
        )
        return await self._repository.create(video.id, content_markdown)
