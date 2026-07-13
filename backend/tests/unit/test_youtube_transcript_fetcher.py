from unittest.mock import MagicMock, patch

import pytest
from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.core.exceptions import ExternalServiceError
from app.services.youtube_transcript_fetcher import YouTubeTranscriptFetcher

# The real exceptions require version-specific constructor args (video_id,
# language codes, etc). Since we only need something `isinstance`-compatible
# for the fetcher's except clauses, subclass with a no-arg __init__ instead
# of guessing the real signature.


class _NoTranscriptFound(NoTranscriptFound):
    def __init__(self):
        Exception.__init__(self, "no transcript found")


class _TranscriptsDisabled(TranscriptsDisabled):
    def __init__(self):
        Exception.__init__(self, "transcripts disabled")


class _VideoUnavailable(VideoUnavailable):
    def __init__(self):
        Exception.__init__(self, "video unavailable")


class _CouldNotRetrieveTranscript(CouldNotRetrieveTranscript):
    def __init__(self):
        Exception.__init__(self, "could not retrieve")


FAKE_SEGMENTS = [
    {"text": "Hello", "start": 0.0, "duration": 2.0},
    {"text": "world", "start": 2.0, "duration": 1.5},
]


def _mock_transcript(language_code, is_generated=False, is_translatable=False, translated=None):
    transcript = MagicMock()
    transcript.language_code = language_code
    transcript.is_generated = is_generated
    transcript.is_translatable = is_translatable
    transcript.fetch.return_value = FAKE_SEGMENTS
    if translated is not None:
        transcript.translate.return_value = translated
    return transcript


def test_prefers_manually_created_transcript_in_requested_language():
    en_manual = _mock_transcript("en", is_generated=False)
    transcript_list = MagicMock()
    transcript_list.find_manually_created_transcript.return_value = en_manual

    with patch(
        "app.services.youtube_transcript_fetcher.YouTubeTranscriptApi.list_transcripts",
        return_value=transcript_list,
    ):
        result = YouTubeTranscriptFetcher().fetch("dQw4w9WgXcQ")

    assert result.language == "en"
    assert result.is_auto_generated is False
    assert result.is_translated is False
    assert result.full_text == "Hello world"
    assert len(result.segments) == 2


def test_falls_back_to_generated_transcript_when_no_manual_one_exists():
    en_auto = _mock_transcript("en", is_generated=True)
    transcript_list = MagicMock()
    transcript_list.find_manually_created_transcript.side_effect = _NoTranscriptFound()
    transcript_list.find_generated_transcript.return_value = en_auto

    with patch(
        "app.services.youtube_transcript_fetcher.YouTubeTranscriptApi.list_transcripts",
        return_value=transcript_list,
    ):
        result = YouTubeTranscriptFetcher().fetch("dQw4w9WgXcQ")

    assert result.is_auto_generated is True
    assert result.language == "en"


def test_translates_to_english_when_source_is_translatable():
    en_translated = _mock_transcript("en")
    es_manual = _mock_transcript("es", is_translatable=True, translated=en_translated)

    transcript_list = MagicMock()
    transcript_list.find_manually_created_transcript.return_value = es_manual

    with patch(
        "app.services.youtube_transcript_fetcher.YouTubeTranscriptApi.list_transcripts",
        return_value=transcript_list,
    ):
        result = YouTubeTranscriptFetcher().fetch("dQw4w9WgXcQ", translate_to_english=True)

    es_manual.translate.assert_called_once_with("en")
    assert result.is_translated is True
    assert result.source_language == "es"
    assert result.language == "en"


def test_keeps_original_language_when_not_translatable():
    es_manual = _mock_transcript("es", is_translatable=False)

    transcript_list = MagicMock()
    transcript_list.find_manually_created_transcript.return_value = es_manual

    with patch(
        "app.services.youtube_transcript_fetcher.YouTubeTranscriptApi.list_transcripts",
        return_value=transcript_list,
    ):
        result = YouTubeTranscriptFetcher().fetch("dQw4w9WgXcQ", translate_to_english=True)

    es_manual.translate.assert_not_called()
    assert result.is_translated is False
    assert result.language == "es"


def test_transcripts_disabled_raises_external_service_error():
    with patch(
        "app.services.youtube_transcript_fetcher.YouTubeTranscriptApi.list_transcripts",
        side_effect=_TranscriptsDisabled(),
    ):
        with pytest.raises(ExternalServiceError):
            YouTubeTranscriptFetcher().fetch("dQw4w9WgXcQ")


def test_video_unavailable_raises_external_service_error():
    with patch(
        "app.services.youtube_transcript_fetcher.YouTubeTranscriptApi.list_transcripts",
        side_effect=_VideoUnavailable(),
    ):
        with pytest.raises(ExternalServiceError):
            YouTubeTranscriptFetcher().fetch("dQw4w9WgXcQ")


def test_no_transcript_available_in_any_language_raises_external_service_error():
    transcript_list = MagicMock()
    transcript_list.find_manually_created_transcript.side_effect = _NoTranscriptFound()
    transcript_list.find_generated_transcript.side_effect = _NoTranscriptFound()
    transcript_list.__iter__.return_value = iter([])

    with patch(
        "app.services.youtube_transcript_fetcher.YouTubeTranscriptApi.list_transcripts",
        return_value=transcript_list,
    ):
        with pytest.raises(ExternalServiceError):
            YouTubeTranscriptFetcher().fetch("dQw4w9WgXcQ")
