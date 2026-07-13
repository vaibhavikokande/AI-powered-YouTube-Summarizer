import uuid
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_provider import LLMProvider
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.chat import ChatSession
from app.models.enums import ChatRole
from app.models.transcript import Transcript
from app.models.video import Video
from app.prompts.chat_prompts import rag_context_block, rag_system_prompt
from app.repositories.chat_repository import ChatRepository
from app.services.rag_service import RagService


class ChatService:
    """Orchestrates RAG chat: retrieve relevant transcript chunks, build a
    prompt with prior conversation history, and stream the LLM's answer —
    persisting both sides of the exchange once the full answer is assembled.
    """

    def __init__(
        self,
        session: AsyncSession,
        rag_service: RagService | None = None,
        llm_provider: LLMProvider | None = None,
    ):
        self._repository = ChatRepository(session)
        self._rag_service = rag_service or RagService()
        self._llm = llm_provider or LLMProvider()

    async def get_or_create_session(
        self, video: Video, session_id: uuid.UUID | None, user_id: uuid.UUID | None = None
    ) -> ChatSession:
        if session_id is not None:
            chat_session = await self._repository.get_session(session_id)
            if chat_session is None:
                raise NotFoundError(f"Chat session {session_id} not found.")
            # Anonymous sessions (user_id is None) are continuable by anyone
            # holding the id; sessions owned by a user are not.
            if chat_session.user_id is not None and chat_session.user_id != user_id:
                raise ForbiddenError("You do not have access to this chat session.")
            return chat_session
        return await self._repository.create_session(video.id, user_id)

    async def ask(
        self, video: Video, transcript: Transcript, chat_session: ChatSession, question: str
    ) -> AsyncIterator[str]:
        await self._rag_service.ensure_indexed(video.id, transcript)
        relevant_chunks = await self._rag_service.retrieve_relevant_chunks(video.id, question)

        # Fetch history *before* persisting this question, so it isn't duplicated
        # both in the history and as the final appended HumanMessage below.
        history = await self._repository.list_messages(chat_session.id)

        context = rag_context_block([(c.start_seconds, c.text) for c in relevant_chunks])
        messages = [SystemMessage(content=f"{rag_system_prompt(video.title)}\n\n{context}")]
        for msg in history:
            messages.append(
                HumanMessage(content=msg.content)
                if msg.role == ChatRole.USER
                else AIMessage(content=msg.content)
            )
        messages.append(HumanMessage(content=question))

        await self._repository.add_message(chat_session.id, ChatRole.USER, question)

        answer_parts: list[str] = []
        async for token in self._llm.stream_text(messages):
            answer_parts.append(token)
            yield token

        await self._repository.add_message(chat_session.id, ChatRole.ASSISTANT, "".join(answer_parts))
