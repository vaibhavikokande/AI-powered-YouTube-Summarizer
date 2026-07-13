import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.enums import QuizQuestionType, SummaryType
from app.tasks.content_tasks import (
    _generate_faq,
    _generate_flashcards,
    _generate_notes,
    _generate_quiz,
    _summarize_video,
)


class _FakeSessionCM:
    """Mimics `async with AsyncSessionLocal() as session:` without a real engine."""

    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *args):
        return False


def _patch_session():
    return patch(
        "app.tasks.content_tasks.AsyncSessionLocal", return_value=_FakeSessionCM(MagicMock())
    )


def _fake_video():
    video = MagicMock()
    video.id = uuid.uuid4()
    video.youtube_video_id = "dQw4w9WgXcQ"
    return video


def _fake_summary():
    summary = MagicMock()
    summary.id = uuid.uuid4()
    summary.video_id = uuid.uuid4()
    summary.summary_type = SummaryType.MEDIUM
    summary.content = "content"
    summary.key_takeaways = {}
    summary.timestamped_sections = []
    summary.topics = {}
    summary.mindmap_markdown = None
    summary.llm_provider = "claude"
    summary.created_at = datetime.now(timezone.utc)
    return summary


async def test_summarize_video_records_history_when_user_id_given():
    video = _fake_video()
    summary = _fake_summary()

    with (
        _patch_session(),
        patch("app.tasks.content_tasks.VideoService") as MockVideoService,
        patch("app.tasks.content_tasks.TranscriptService") as MockTranscriptService,
        patch("app.tasks.content_tasks.SummarizationService") as MockSummarizationService,
        patch("app.tasks.content_tasks.HistoryService") as MockHistoryService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=video)
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=MagicMock()
        )
        MockSummarizationService.return_value.summarize = AsyncMock(return_value=[summary])
        MockHistoryService.return_value.record_view = AsyncMock()

        result = await _summarize_video(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            [SummaryType.MEDIUM],
            "en",
            False,
            str(uuid.uuid4()),
        )

    assert len(result) == 1
    assert result[0]["content"] == "content"
    MockHistoryService.return_value.record_view.assert_called_once()


async def test_summarize_video_skips_history_when_anonymous():
    video = _fake_video()

    with (
        _patch_session(),
        patch("app.tasks.content_tasks.VideoService") as MockVideoService,
        patch("app.tasks.content_tasks.TranscriptService") as MockTranscriptService,
        patch("app.tasks.content_tasks.SummarizationService") as MockSummarizationService,
        patch("app.tasks.content_tasks.HistoryService") as MockHistoryService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=video)
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=MagicMock()
        )
        MockSummarizationService.return_value.summarize = AsyncMock(return_value=[])

        await _summarize_video(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ", [SummaryType.MEDIUM], "en", False, None
        )

    MockHistoryService.return_value.record_view.assert_not_called()


async def test_generate_quiz_returns_serialized_dict():
    quiz = MagicMock()
    quiz.id = uuid.uuid4()
    quiz.title = "Test Quiz"
    quiz.questions = []

    with (
        _patch_session(),
        patch("app.tasks.content_tasks.VideoService") as MockVideoService,
        patch("app.tasks.content_tasks.TranscriptService") as MockTranscriptService,
        patch("app.tasks.content_tasks.QuizService") as MockQuizService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=_fake_video())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=MagicMock()
        )
        MockQuizService.return_value.generate = AsyncMock(return_value=quiz)

        result = await _generate_quiz(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ", [QuizQuestionType.MCQ], 5
        )

    assert result["title"] == "Test Quiz"
    assert result["questions"] == []


async def test_generate_flashcards_returns_serialized_list():
    card = MagicMock()
    card.id = uuid.uuid4()
    card.question = "Q?"
    card.answer = "A."

    with (
        _patch_session(),
        patch("app.tasks.content_tasks.VideoService") as MockVideoService,
        patch("app.tasks.content_tasks.TranscriptService") as MockTranscriptService,
        patch("app.tasks.content_tasks.FlashcardService") as MockFlashcardService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=_fake_video())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=MagicMock()
        )
        MockFlashcardService.return_value.generate = AsyncMock(return_value=[card])

        result = await _generate_flashcards("https://www.youtube.com/watch?v=dQw4w9WgXcQ", 5)

    assert result == [{"id": str(card.id), "question": "Q?", "answer": "A."}]


async def test_generate_faq_returns_serialized_list():
    item = MagicMock()
    item.id = uuid.uuid4()
    item.question = "Q?"
    item.answer = "A."
    item.created_at = datetime.now(timezone.utc)

    with (
        _patch_session(),
        patch("app.tasks.content_tasks.VideoService") as MockVideoService,
        patch("app.tasks.content_tasks.TranscriptService") as MockTranscriptService,
        patch("app.tasks.content_tasks.FAQService") as MockFAQService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=_fake_video())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=MagicMock()
        )
        MockFAQService.return_value.generate = AsyncMock(return_value=[item])

        result = await _generate_faq("https://www.youtube.com/watch?v=dQw4w9WgXcQ", 5)

    assert len(result) == 1
    assert result[0]["question"] == "Q?"


async def test_generate_notes_returns_serialized_dict():
    note = MagicMock()
    note.id = uuid.uuid4()
    note.video_id = uuid.uuid4()
    note.content_markdown = "## Notes"
    note.created_at = datetime.now(timezone.utc)

    with (
        _patch_session(),
        patch("app.tasks.content_tasks.VideoService") as MockVideoService,
        patch("app.tasks.content_tasks.TranscriptService") as MockTranscriptService,
        patch("app.tasks.content_tasks.NotesService") as MockNotesService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=_fake_video())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=MagicMock()
        )
        MockNotesService.return_value.generate = AsyncMock(return_value=note)

        result = await _generate_notes("https://www.youtube.com/watch?v=dQw4w9WgXcQ", None)

    assert result["content_markdown"] == "## Notes"
