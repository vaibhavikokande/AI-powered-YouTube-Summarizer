import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.chat_service import ChatService
from app.services.transcript_service import TranscriptService
from app.services.video_service import VideoService

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    url: str = Field(..., description="A YouTube video, shorts, or youtu.be URL")
    session_id: uuid.UUID | None = Field(
        None, description="Existing chat session id to continue; omit to start a new one"
    )
    message: str = Field(..., min_length=1)


@router.post("/chat")
async def chat_with_video(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    """Ask a question about a video's content; streams the answer as SSE.

    Each event while streaming is `data: {"token": "..."}`; the final event
    is `data: {"session_id": "...", "done": true}` so the frontend can send
    follow-up questions against the same session_id (conversation memory).
    """
    video = await VideoService(db).get_or_fetch_video(request.url)
    transcript = await TranscriptService(db).get_or_fetch_transcript(
        video_id=video.id, youtube_video_id=video.youtube_video_id
    )
    chat_service = ChatService(db)
    chat_session = await chat_service.get_or_create_session(video, request.session_id)

    async def event_stream():
        async for token in chat_service.ask(video, transcript, chat_session, request.message):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'session_id': str(chat_session.id), 'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
