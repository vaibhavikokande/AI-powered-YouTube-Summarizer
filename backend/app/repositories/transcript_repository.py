import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import Transcript


class TranscriptRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_video_id(self, video_id: uuid.UUID) -> Transcript | None:
        result = await self._session.execute(
            select(Transcript).where(Transcript.video_id == video_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        video_id: uuid.UUID,
        *,
        language: str,
        is_auto_generated: bool,
        is_translated: bool,
        source_language: str | None,
        full_text: str,
        segments: list[dict],
    ) -> Transcript:
        transcript = Transcript(
            video_id=video_id,
            language=language,
            is_auto_generated=is_auto_generated,
            is_translated=is_translated,
            source_language=source_language,
            full_text=full_text,
            segments=segments,
        )
        self._session.add(transcript)
        await self._session.commit()
        await self._session.refresh(transcript)
        return transcript

    async def update_chunk_summaries(self, transcript_id: uuid.UUID, chunk_summaries_text: str) -> None:
        transcript = await self._session.get(Transcript, transcript_id)
        transcript.chunk_summaries_text = chunk_summaries_text
        await self._session.commit()
