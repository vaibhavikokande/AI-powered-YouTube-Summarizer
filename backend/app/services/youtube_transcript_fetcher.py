import logging
from dataclasses import dataclass
from typing import Any

from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

from app.core.exceptions import ExternalServiceError
from app.schemas.transcript import TranscriptSegment

logger = logging.getLogger(__name__)


@dataclass
class FetchedTranscript:
    """Result of fetching a transcript from YouTube — not yet persisted."""

    language: str
    source_language: str | None
    is_auto_generated: bool
    is_translated: bool
    full_text: str
    segments: list[TranscriptSegment]


class YouTubeTranscriptFetcher:
    """Wraps youtube-transcript-api: official + auto-generated captions,
    with language fallback and translation to English when the source
    transcript isn't already in the requested language.
    """

    def fetch(
        self,
        youtube_video_id: str,
        preferred_language: str = "en",
        translate_to_english: bool = True,
    ) -> FetchedTranscript:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(youtube_video_id)
            transcript = self._select_transcript(transcript_list, preferred_language)

            source_language = transcript.language_code
            is_auto_generated = transcript.is_generated
            is_translated = False

            if (
                translate_to_english
                and source_language != "en"
                and transcript.is_translatable
            ):
                transcript = transcript.translate("en")
                is_translated = True

            fetched_segments = transcript.fetch()
        except TranscriptsDisabled as exc:
            raise ExternalServiceError("Transcripts are disabled for this video.") from exc
        except VideoUnavailable as exc:
            raise ExternalServiceError("This video is unavailable.") from exc
        except CouldNotRetrieveTranscript as exc:
            logger.warning("Could not retrieve transcript for %s: %s", youtube_video_id, exc)
            raise ExternalServiceError("Could not retrieve a transcript for this video.") from exc

        segments = [
            TranscriptSegment(start=seg["start"], duration=seg["duration"], text=seg["text"])
            for seg in fetched_segments
        ]
        full_text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())

        return FetchedTranscript(
            language=transcript.language_code,
            source_language=source_language if is_translated else None,
            is_auto_generated=is_auto_generated,
            is_translated=is_translated,
            full_text=full_text,
            segments=segments,
        )

    @staticmethod
    def _select_transcript(transcript_list: Any, preferred_language: str) -> Any:
        """Prefer a human-made transcript in the requested language, then an
        auto-generated one in that language, then whatever is available.
        """
        try:
            return transcript_list.find_manually_created_transcript([preferred_language])
        except NoTranscriptFound:
            pass

        try:
            return transcript_list.find_generated_transcript([preferred_language])
        except NoTranscriptFound:
            pass

        available = list(transcript_list)
        if not available:
            raise ExternalServiceError("No transcript is available for this video in any language.")
        return available[0]
