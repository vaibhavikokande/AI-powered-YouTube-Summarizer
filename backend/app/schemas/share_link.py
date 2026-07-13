import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShareLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    token: str
    summary_id: uuid.UUID
    expires_at: datetime | None
    created_at: datetime
