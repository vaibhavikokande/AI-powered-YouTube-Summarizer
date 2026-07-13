import asyncio
import uuid

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_provider import LLMProvider
from app.models.enums import SummaryType
from app.models.summary import Summary
from app.models.transcript import Transcript
from app.models.video import Video
from app.prompts.summary_prompts import (
    chunk_summary_prompt,
    key_takeaways_prompt,
    reduce_summary_prompt,
    timestamped_sections_prompt,
    topics_prompt,
)
from app.repositories.summary_repository import SummaryRepository
from app.schemas.summary import KeyTakeaways, TimestampedSectionList, Topics
from app.schemas.transcript import TranscriptSegment
from app.utils.chunking import TranscriptChunk, chunk_transcript


class SummarizationService:
    """Map-reduce summarization: each transcript chunk is summarized in
    isolation (map), then the chunk summaries are combined into whichever
    summary lengths/styles were requested, plus key takeaways, topics, and
    timestamped sections (reduce) — all sharing the same map step regardless
    of how many summary types are requested.
    """

    def __init__(self, session: AsyncSession, llm_provider: LLMProvider | None = None):
        self._repository = SummaryRepository(session)
        self._llm = llm_provider or LLMProvider()

    async def summarize(
        self,
        video: Video,
        transcript: Transcript,
        summary_types: list[SummaryType],
        user_id: uuid.UUID | None = None,
    ) -> list[Summary]:
        results: dict[SummaryType, Summary] = {}
        missing_types: list[SummaryType] = []

        for summary_type in summary_types:
            existing = await self._repository.get_by_video_and_type(video.id, summary_type)
            if existing is not None:
                results[summary_type] = existing
            else:
                missing_types.append(summary_type)

        if not missing_types:
            return [results[st] for st in summary_types]

        segments = [TranscriptSegment(**seg) for seg in transcript.segments]
        chunks = chunk_transcript(segments)
        if not chunks:
            raise ValueError("Transcript has no usable content to summarize.")

        chunk_summaries = await asyncio.gather(*[self._summarize_chunk(c) for c in chunks])
        combined = "\n\n".join(chunk_summaries)

        key_takeaways, topics, timestamped_sections = await asyncio.gather(
            self._extract_key_takeaways(combined),
            self._extract_topics(combined),
            self._extract_timestamped_sections(chunks, chunk_summaries),
        )

        for summary_type in missing_types:
            content = await self._reduce_summary(combined, summary_type, video.title)
            summary = await self._repository.create(
                video_id=video.id,
                user_id=user_id,
                summary_type=summary_type,
                content=content,
                key_takeaways=key_takeaways.model_dump(),
                timestamped_sections=[s.model_dump() for s in timestamped_sections.sections],
                topics=topics.model_dump(),
                llm_provider=self._llm.provider_name,
            )
            results[summary_type] = summary

        return [results[st] for st in summary_types]

    async def _summarize_chunk(self, chunk: TranscriptChunk) -> str:
        return await self._llm.generate_text([HumanMessage(content=chunk_summary_prompt(chunk.text))])

    async def _reduce_summary(
        self, combined: str, summary_type: SummaryType, video_title: str | None
    ) -> str:
        return await self._llm.generate_text(
            [HumanMessage(content=reduce_summary_prompt(combined, summary_type, video_title))]
        )

    async def _extract_key_takeaways(self, combined: str) -> KeyTakeaways:
        return await self._llm.generate_structured(
            [HumanMessage(content=key_takeaways_prompt(combined))], KeyTakeaways
        )

    async def _extract_topics(self, combined: str) -> Topics:
        return await self._llm.generate_structured(
            [HumanMessage(content=topics_prompt(combined))], Topics
        )

    async def _extract_timestamped_sections(
        self, chunks: list[TranscriptChunk], chunk_summaries: list[str]
    ) -> TimestampedSectionList:
        timestamped = list(zip((c.start_seconds for c in chunks), chunk_summaries))
        return await self._llm.generate_structured(
            [HumanMessage(content=timestamped_sections_prompt(timestamped))], TimestampedSectionList
        )
