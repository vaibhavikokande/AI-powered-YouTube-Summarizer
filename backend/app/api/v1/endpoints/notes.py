from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user_optional
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.job import JobEnqueuedResponse
from app.schemas.note import NoteGenerateRequest
from app.tasks.content_tasks import generate_notes_task
from app.utils.youtube import extract_video_id

router = APIRouter(tags=["notes"])


@router.post("/notes", response_model=JobEnqueuedResponse)
@limiter.limit("10/minute")
async def generate_notes(
    request: Request,
    body: NoteGenerateRequest,
    current_user: User | None = Depends(get_current_user_optional),
) -> JobEnqueuedResponse:
    """Enqueues notes generation; poll GET /jobs/{task_id} for the result."""
    extract_video_id(body.url)

    user_id = current_user.id if current_user else None
    task = generate_notes_task.delay(body.url, str(user_id) if user_id else None)
    return JobEnqueuedResponse(task_id=task.id)
