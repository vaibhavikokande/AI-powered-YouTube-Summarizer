import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import Transcript
from app.repositories.transcript_repository import TranscriptRepository
from app.services.youtube_transcript_fetcher import YouTubeTranscriptFetcher


class TranscriptService:
    def __init__(self, session: AsyncSession):
        self._repository = TranscriptRepository(session)
        self._fetcher = YouTubeTranscriptFetcher()

    async def get_or_fetch_transcript(
        self,
        video_id: uuid.UUID,
        youtube_video_id: str,
        preferred_language: str = "en",
        translate_to_english: bool = True,
    ) -> Transcript:
        """Return the stored transcript for this video, or fetch + persist it.

        One transcript row is kept per video — whichever language ends up
        being used for downstream summarization (English, by default, via
        translation) — rather than storing every language variant.
        """
        existing = await self._repository.get_by_video_id(video_id)
        if existing is not None:
            return existing

        fetched = await asyncio.to_thread(
            self._fetcher.fetch, youtube_video_id, preferred_language, translate_to_english
        )

        return await self._repository.create(
            video_id,
            language=fetched.language,
            is_auto_generated=fetched.is_auto_generated,
            is_translated=fetched.is_translated,
            source_language=fetched.source_language,
            full_text=fetched.full_text,
            segments=[segment.model_dump() for segment in fetched.segments],
        )
