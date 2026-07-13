import asyncio

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_provider import LLMProvider
from app.models.transcript import Transcript
from app.prompts.summary_prompts import chunk_summary_prompt
from app.repositories.transcript_repository import TranscriptRepository
from app.schemas.transcript import TranscriptSegment
from app.utils.chunking import TranscriptChunk, chunk_transcript


class ContentPrepService:
    """Produces the map-step output every content generator builds on:
    each transcript chunk summarized once, combined into one string.

    Computed once per transcript and cached on `Transcript.chunk_summaries_text`
    — asking for flashcards after already generating a summary (or vice
    versa) reuses the cached text instead of re-running the LLM map step.
    """

    def __init__(self, session: AsyncSession, llm_provider: LLMProvider | None = None):
        self._repository = TranscriptRepository(session)
        self._llm = llm_provider or LLMProvider()

    async def get_combined_summary(self, transcript: Transcript) -> str:
        if transcript.chunk_summaries_text:
            return transcript.chunk_summaries_text

        combined, _chunks, _chunk_summaries = await self._map_and_cache(transcript)
        return combined

    async def get_combined_summary_with_chunks(
        self, transcript: Transcript
    ) -> tuple[str, list[TranscriptChunk], list[str]]:
        """Same as `get_combined_summary`, but also returns per-chunk
        summaries with their timestamps. Only needed for timestamped-section
        generation, which — like this method — only runs once per video
        (see `SummarizationService`), so this always computes fresh rather
        than trying to reconstruct per-chunk boundaries from cached text.
        """
        return await self._map_and_cache(transcript)

    async def _map_and_cache(
        self, transcript: Transcript
    ) -> tuple[str, list[TranscriptChunk], list[str]]:
        segments = [TranscriptSegment(**seg) for seg in transcript.segments]
        chunks = chunk_transcript(segments)
        if not chunks:
            raise ValueError("Transcript has no usable content to work with.")

        chunk_summaries = list(await asyncio.gather(*[self._summarize_chunk(c.text) for c in chunks]))
        combined = "\n\n".join(chunk_summaries)

        await self._repository.update_chunk_summaries(transcript.id, combined)
        transcript.chunk_summaries_text = combined

        return combined, chunks, chunk_summaries

    async def _summarize_chunk(self, chunk_text: str) -> str:
        return await self._llm.generate_text([HumanMessage(content=chunk_summary_prompt(chunk_text))])
