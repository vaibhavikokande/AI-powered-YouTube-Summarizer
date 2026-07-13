from celery.result import AsyncResult
from fastapi import APIRouter

from app.schemas.job import JobStatusResponse
from app.services.celery_app import celery_app

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{task_id}", response_model=JobStatusResponse)
async def get_job_status(task_id: str) -> JobStatusResponse:
    """Poll a background job enqueued by /summarize, /quiz, /flashcards,
    /faq, or /notes. `status` is one of Celery's states (PENDING, STARTED,
    SUCCESS, FAILURE, RETRY); `result` is populated only once SUCCESS.
    """
    result = AsyncResult(task_id, app=celery_app)
    response = JobStatusResponse(task_id=task_id, status=result.status)
    if result.successful():
        response.result = result.result
    elif result.failed():
        response.error = str(result.result)
    return response
