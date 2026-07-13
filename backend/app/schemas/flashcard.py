import uuid

from pydantic import BaseModel, ConfigDict


class FlashcardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    answer: str
