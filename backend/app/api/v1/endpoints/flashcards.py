from fastapi import APIRouter, Request

from app.middleware.rate_limit import limiter
from app.schemas.flashcard import FlashcardGenerateRequest
from app.schemas.job import JobEnqueuedResponse
from app.tasks.content_tasks import generate_flashcards_task
from app.utils.youtube import extract_video_id

router = APIRouter(tags=["flashcards"])


@router.post("/flashcards", response_model=JobEnqueuedResponse)
@limiter.limit("10/minute")
async def generate_flashcards(
    request: Request, body: FlashcardGenerateRequest
) -> JobEnqueuedResponse:
    """Enqueues flashcard generation; poll GET /jobs/{task_id} for the result."""
    extract_video_id(body.url)

    task = generate_flashcards_task.delay(body.url, body.count)
    return JobEnqueuedResponse(task_id=task.id)
