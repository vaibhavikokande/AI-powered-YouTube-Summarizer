from typing import Any

from pydantic import BaseModel


class JobEnqueuedResponse(BaseModel):
    task_id: str
    status: str = "queued"


class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Any = None
    error: str | None = None
