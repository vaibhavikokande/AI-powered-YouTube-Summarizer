from fastapi import APIRouter, Request

from app.middleware.rate_limit import limiter
from app.schemas.job import JobEnqueuedResponse
from app.schemas.quiz import QuizGenerateRequest
from app.tasks.content_tasks import generate_quiz_task
from app.utils.youtube import extract_video_id

router = APIRouter(tags=["quiz"])


@router.post("/quiz", response_model=JobEnqueuedResponse)
@limiter.limit("10/minute")
async def generate_quiz(request: Request, body: QuizGenerateRequest) -> JobEnqueuedResponse:
    """Enqueues quiz generation; poll GET /jobs/{task_id} for the result."""
    extract_video_id(body.url)

    task = generate_quiz_task.delay(
        body.url, [t.value for t in body.question_types], body.count
    )
    return JobEnqueuedResponse(task_id=task.id)
