from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user_optional
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.job import JobEnqueuedResponse
from app.schemas.summary import SummarizeRequest
from app.tasks.content_tasks import summarize_video_task
from app.utils.youtube import extract_video_id

router = APIRouter(tags=["summarize"])


@router.post("/summarize", response_model=JobEnqueuedResponse)
@limiter.limit("10/minute")
async def summarize_video(
    request: Request,
    body: SummarizeRequest,
    current_user: User | None = Depends(get_current_user_optional),
) -> JobEnqueuedResponse:
    """Validates the URL and enqueues a background job; poll GET /jobs/{task_id}
    for the resulting summaries.

    Moved off the request path in Step 11 — map-reduce summarization of a
    multi-hour transcript can take minutes, which is too long to hold an
    HTTP connection open for. Works anonymously; if authenticated, the job
    records a GET /history view once it completes. Rate-limited tighter
    than the app default since this is the most LLM-cost-heavy endpoint.
    """
    extract_video_id(body.url)  # fail fast on a malformed URL before enqueuing

    user_id = current_user.id if current_user else None
    task = summarize_video_task.delay(
        body.url,
        [t.value for t in body.summary_types],
        body.language,
        body.include_mindmap,
        str(user_id) if user_id else None,
    )
    return JobEnqueuedResponse(task_id=task.id)
