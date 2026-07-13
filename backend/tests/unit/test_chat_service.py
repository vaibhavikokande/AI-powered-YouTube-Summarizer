import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.models.enums import ChatRole
from app.services.chat_service import ChatService


def _fake_video():
    video = MagicMock()
    video.id = uuid.uuid4()
    video.title = "Test Video"
    return video


async def _fake_stream(messages):
    for token in ["Hel", "lo"]:
        yield token


def _service_with_mocks() -> ChatService:
    rag_service = MagicMock()
    rag_service.ensure_indexed = AsyncMock()
    rag_service.retrieve_relevant_chunks = AsyncMock(return_value=[])

    llm = MagicMock()
    llm.stream_text = _fake_stream

    service = ChatService(session=MagicMock(), rag_service=rag_service, llm_provider=llm)
    service._repository = MagicMock()
    return service


async def test_get_or_create_session_returns_existing_session():
    service = _service_with_mocks()
    existing = MagicMock()
    service._repository.get_session = AsyncMock(return_value=existing)

    result = await service.get_or_create_session(_fake_video(), session_id=uuid.uuid4())

    assert result is existing


async def test_get_or_create_session_raises_when_session_id_not_found():
    service = _service_with_mocks()
    service._repository.get_session = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await service.get_or_create_session(_fake_video(), session_id=uuid.uuid4())


async def test_get_or_create_session_creates_new_session_when_no_id_given():
    service = _service_with_mocks()
    new_session = MagicMock()
    service._repository.create_session = AsyncMock(return_value=new_session)

    result = await service.get_or_create_session(_fake_video(), session_id=None)

    assert result is new_session
    service._repository.create_session.assert_called_once()


async def test_ask_streams_tokens_and_persists_both_messages_in_order():
    service = _service_with_mocks()
    service._repository.list_messages = AsyncMock(return_value=[])
    service._repository.add_message = AsyncMock()

    video = _fake_video()
    transcript = MagicMock()
    chat_session = MagicMock()
    chat_session.id = uuid.uuid4()

    tokens = [t async for t in service.ask(video, transcript, chat_session, "What is X?")]

    assert tokens == ["Hel", "lo"]
    service._rag_service.ensure_indexed.assert_called_once_with(video.id, transcript)
    service._rag_service.retrieve_relevant_chunks.assert_called_once_with(video.id, "What is X?")

    add_message_calls = service._repository.add_message.call_args_list
    assert len(add_message_calls) == 2
    assert add_message_calls[0].args == (chat_session.id, ChatRole.USER, "What is X?")
    assert add_message_calls[1].args == (chat_session.id, ChatRole.ASSISTANT, "Hello")
