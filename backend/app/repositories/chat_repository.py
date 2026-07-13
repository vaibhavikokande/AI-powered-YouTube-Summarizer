import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession
from app.models.enums import ChatRole


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_session(self, session_id: uuid.UUID) -> ChatSession | None:
        result = await self._session.execute(select(ChatSession).where(ChatSession.id == session_id))
        return result.scalar_one_or_none()

    async def create_session(
        self, video_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> ChatSession:
        chat_session = ChatSession(video_id=video_id, user_id=user_id)
        self._session.add(chat_session)
        await self._session.commit()
        await self._session.refresh(chat_session)
        return chat_session

    async def list_messages(self, session_id: uuid.UUID) -> list[ChatMessage]:
        result = await self._session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def add_message(self, session_id: uuid.UUID, role: ChatRole, content: str) -> ChatMessage:
        message = ChatMessage(session_id=session_id, role=role, content=content)
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message
