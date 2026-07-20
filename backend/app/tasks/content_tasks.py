"""Celery tasks for the content-generation endpoints.

Each task opens its own DB session (a Celery worker is a separate process
from the FastAPI app, so it can't reuse a request-scoped session) and runs
the same service pipeline the endpoint used to run inline before Step 11.
"""

import asyncio
import uuid
from collections.abc import Coroutine
from typing import TypeVar

from app.core.exceptions import ExternalServiceError
from app.db.session import AsyncSessionLocal, engine
from app.models.enums import QuizQuestionType, SummaryType
from app.services.celery_app import celery_app
from app.services.faq_service import FAQService
from app.services.flashcard_service import FlashcardService
from app.services.history_service import HistoryService
from app.services.notes_service import NotesService
from app.services.quiz_service import QuizService
from app.services.summarization_service import SummarizationService
from app.services.transcript_service import TranscriptService
from app.services.video_service import VideoService
from app.tasks.serialization import (
    faq_item_to_dict,
    flashcard_to_dict,
    note_to_dict,
    quiz_to_dict,
    summary_to_dict,
)

# Retries only genuinely transient failures (external service hiccups,
# connection blips) with exponential backoff — NOT ValidationAppError or
# NotFoundError, where retrying identical input just wastes time before
# failing the same way again.
_RETRY_KWARGS = {
    "autoretry_for": (ExternalServiceError, ConnectionError, TimeoutError, OSError),
    "retry_kwargs": {"max_retries": 2},
    "retry_backoff": True,
    "retry_backoff_max": 60,
    "retry_jitter": True,
}

_T = TypeVar("_T")


def _run_task(coro: Coroutine[None, None, _T]) -> _T:
    """Runs a task coroutine in its own event loop, then disposes the shared
    async engine's connection pool before that loop closes.

    `engine` (app/db/session.py) is a process-wide singleton also used by the
    FastAPI app, where a single long-lived event loop makes pooling safe. A
    Celery worker instead calls asyncio.run() per task, each spinning up and
    tearing down its own loop — without disposing here, pooled asyncpg
    connections from one task's loop get reused by the next task's loop and
    fail with "AttributeError: 'NoneType' object has no attribute 'send'"
    once their old loop's proactor is gone.
    """

    async def _run() -> _T:
        try:
            return await coro
        finally:
            await engine.dispose()

    return asyncio.run(_run())


@celery_app.task(name="tasks.summarize_video", bind=True, **_RETRY_KWARGS)
def summarize_video_task(
    self,
    url: str,
    summary_types: list[str],
    language: str,
    include_mindmap: bool,
    user_id: str | None,
) -> list[dict]:
    return _run_task(
        _summarize_video(
            url, [SummaryType(t) for t in summary_types], language, include_mindmap, user_id
        )
    )


async def _summarize_video(
    url: str,
    summary_types: list[SummaryType],
    language: str,
    include_mindmap: bool,
    user_id: str | None,
) -> list[dict]:
    async with AsyncSessionLocal() as session:
        uid = uuid.UUID(user_id) if user_id else None
        video = await VideoService(session).get_or_fetch_video(url, user_id=uid)
        transcript = await TranscriptService(session).get_or_fetch_transcript(
            video_id=video.id, youtube_video_id=video.youtube_video_id, preferred_language=language
        )
        summaries = await SummarizationService(session).summarize(
            video=video,
            transcript=transcript,
            summary_types=summary_types,
            user_id=uid,
            include_mindmap=include_mindmap,
        )

        if uid is not None:
            await HistoryService(session).record_view(uid, video.id)

        return [summary_to_dict(s) for s in summaries]


@celery_app.task(name="tasks.generate_quiz", bind=True, **_RETRY_KWARGS)
def generate_quiz_task(self, url: str, question_types: list[str], count: int) -> dict:
    return _run_task(
        _generate_quiz(url, [QuizQuestionType(t) for t in question_types], count)
    )


async def _generate_quiz(url: str, question_types: list[QuizQuestionType], count: int) -> dict:
    async with AsyncSessionLocal() as session:
        video = await VideoService(session).get_or_fetch_video(url)
        transcript = await TranscriptService(session).get_or_fetch_transcript(
            video_id=video.id, youtube_video_id=video.youtube_video_id
        )
        quiz = await QuizService(session).generate(video, transcript, question_types, count)
        return quiz_to_dict(quiz)


@celery_app.task(name="tasks.generate_flashcards", bind=True, **_RETRY_KWARGS)
def generate_flashcards_task(self, url: str, count: int) -> list[dict]:
    return _run_task(_generate_flashcards(url, count))


async def _generate_flashcards(url: str, count: int) -> list[dict]:
    async with AsyncSessionLocal() as session:
        video = await VideoService(session).get_or_fetch_video(url)
        transcript = await TranscriptService(session).get_or_fetch_transcript(
            video_id=video.id, youtube_video_id=video.youtube_video_id
        )
        flashcards = await FlashcardService(session).generate(video, transcript, count)
        return [flashcard_to_dict(f) for f in flashcards]


@celery_app.task(name="tasks.generate_faq", bind=True, **_RETRY_KWARGS)
def generate_faq_task(self, url: str, count: int) -> list[dict]:
    return _run_task(_generate_faq(url, count))


async def _generate_faq(url: str, count: int) -> list[dict]:
    async with AsyncSessionLocal() as session:
        video = await VideoService(session).get_or_fetch_video(url)
        transcript = await TranscriptService(session).get_or_fetch_transcript(
            video_id=video.id, youtube_video_id=video.youtube_video_id
        )
        faq_items = await FAQService(session).generate(video, transcript, count)
        return [faq_item_to_dict(item) for item in faq_items]


@celery_app.task(name="tasks.generate_notes", bind=True, **_RETRY_KWARGS)
def generate_notes_task(self, url: str, user_id: str | None) -> dict:
    return _run_task(_generate_notes(url, user_id))


async def _generate_notes(url: str, user_id: str | None) -> dict:
    async with AsyncSessionLocal() as session:
        uid = uuid.UUID(user_id) if user_id else None
        video = await VideoService(session).get_or_fetch_video(url)
        transcript = await TranscriptService(session).get_or_fetch_transcript(
            video_id=video.id, youtube_video_id=video.youtube_video_id
        )
        note = await NotesService(session).generate(video, transcript, user_id=uid)
        return note_to_dict(note)
