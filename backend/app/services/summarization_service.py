import asyncio
import uuid

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_provider import LLMProvider
from app.models.enums import SummaryType
from app.models.summary import Summary
from app.models.transcript import Transcript
from app.models.video import Video
from app.prompts.mindmap_prompts import mindmap_prompt
from app.prompts.summary_prompts import (
    key_takeaways_prompt,
    reduce_summary_prompt,
    timestamped_sections_prompt,
    topics_prompt,
)
from app.repositories.summary_repository import SummaryRepository
from app.schemas.summary import KeyTakeaways, TimestampedSectionList, Topics
from app.services.content_prep_service import ContentPrepService
from app.utils.chunking import TranscriptChunk


class SummarizationService:
    """Reduce step of map-reduce summarization: combines the transcript's
    cached chunk summaries (see `ContentPrepService`) into whichever summary
    lengths/styles were requested, plus key takeaways, topics, and
    timestamped sections.

    Key takeaways/topics/timestamped sections are properties of the video,
    not of a specific summary type — they're derived once (on the first
    summary ever generated for a video) and reused across every additional
    summary type requested afterward, rather than re-derived via fresh LLM
    calls each time.
    """

    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider | None = None,
        content_prep: ContentPrepService | None = None,
    ):
        self._repository = SummaryRepository(session)
        self._llm = llm_provider or LLMProvider()
        self._content_prep = content_prep or ContentPrepService(session, self._llm)

    async def summarize(
        self,
        video: Video,
        transcript: Transcript,
        summary_types: list[SummaryType],
        user_id: uuid.UUID | None = None,
        include_mindmap: bool = False,
    ) -> list[Summary]:
        results: dict[SummaryType, Summary] = {}
        missing_types: list[SummaryType] = []

        for summary_type in summary_types:
            existing = await self._repository.get_by_video_and_type(video.id, summary_type)
            if existing is not None:
                results[summary_type] = existing
            else:
                missing_types.append(summary_type)

        if not missing_types and not include_mindmap:
            return [results[st] for st in summary_types]

        any_existing = await self._repository.list_by_video(video.id)

        if any_existing:
            reference = any_existing[0]
            key_takeaways = KeyTakeaways(**reference.key_takeaways)
            topics = Topics(**reference.topics)
            timestamped_sections = TimestampedSectionList(sections=reference.timestamped_sections)
            combined = await self._content_prep.get_combined_summary(transcript)
        else:
            combined, chunks, chunk_summaries = (
                await self._content_prep.get_combined_summary_with_chunks(transcript)
            )
            key_takeaways, topics, timestamped_sections = await self._extract_video_level_content(
                combined, chunks, chunk_summaries
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

        if include_mindmap:
            for summary_type in summary_types:
                summary = results[summary_type]
                if summary.mindmap_markdown is None:
                    summary.mindmap_markdown = await self._generate_mindmap(combined, video.title)
                    await self._repository.update_mindmap(summary.id, summary.mindmap_markdown)

        return [results[st] for st in summary_types]

    async def _extract_video_level_content(
        self, combined: str, chunks: list[TranscriptChunk], chunk_summaries: list[str]
    ) -> tuple[KeyTakeaways, Topics, TimestampedSectionList]:
        return await asyncio.gather(
            self._extract_key_takeaways(combined),
            self._extract_topics(combined),
            self._extract_timestamped_sections(chunks, chunk_summaries),
        )

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

    async def _generate_mindmap(self, combined: str, video_title: str | None) -> str:
        return await self._llm.generate_text(
            [HumanMessage(content=mindmap_prompt(combined, video_title))]
        )
