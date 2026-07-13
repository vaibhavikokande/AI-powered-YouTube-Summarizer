from fastapi import APIRouter, Request

from app.middleware.rate_limit import limiter
from app.schemas.faq import FAQGenerateRequest
from app.schemas.job import JobEnqueuedResponse
from app.tasks.content_tasks import generate_faq_task
from app.utils.youtube import extract_video_id

router = APIRouter(tags=["faq"])


@router.post("/faq", response_model=JobEnqueuedResponse)
@limiter.limit("10/minute")
async def generate_faq(request: Request, body: FAQGenerateRequest) -> JobEnqueuedResponse:
    """Enqueues FAQ generation; poll GET /jobs/{task_id} for the result."""
    extract_video_id(body.url)

    task = generate_faq_task.delay(body.url, body.count)
    return JobEnqueuedResponse(task_id=task.id)
