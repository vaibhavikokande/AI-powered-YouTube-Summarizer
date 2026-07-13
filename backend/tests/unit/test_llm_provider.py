from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.agents.llm_provider import LLMProvider, build_chat_model
from app.core.config import Settings
from app.core.exceptions import ExternalServiceError


def _settings(**overrides) -> Settings:
    defaults = {
        "LLM_PROVIDER": "claude",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "OPENAI_API_KEY": "test-openai-key",
        "GOOGLE_API_KEY": "test-google-key",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_build_chat_model_raises_when_claude_key_missing():
    settings = _settings(LLM_PROVIDER="claude", ANTHROPIC_API_KEY=None)
    with pytest.raises(ExternalServiceError):
        build_chat_model(settings)


def test_build_chat_model_raises_when_openai_key_missing():
    settings = _settings(LLM_PROVIDER="openai", OPENAI_API_KEY=None)
    with pytest.raises(ExternalServiceError):
        build_chat_model(settings)


def test_build_chat_model_raises_when_gemini_key_missing():
    settings = _settings(LLM_PROVIDER="gemini", GOOGLE_API_KEY=None)
    with pytest.raises(ExternalServiceError):
        build_chat_model(settings)


def test_build_chat_model_constructs_claude_client():
    settings = _settings(LLM_PROVIDER="claude")
    with patch("langchain_anthropic.ChatAnthropic") as MockChatAnthropic:
        build_chat_model(settings)
    MockChatAnthropic.assert_called_once()
    assert MockChatAnthropic.call_args.kwargs["model"] == settings.ANTHROPIC_MODEL


def test_build_chat_model_constructs_openai_client():
    settings = _settings(LLM_PROVIDER="openai")
    with patch("langchain_openai.ChatOpenAI") as MockChatOpenAI:
        build_chat_model(settings)
    MockChatOpenAI.assert_called_once()
    assert MockChatOpenAI.call_args.kwargs["model"] == settings.OPENAI_MODEL


def test_build_chat_model_constructs_gemini_client():
    settings = _settings(LLM_PROVIDER="gemini")
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockChatGemini:
        build_chat_model(settings)
    MockChatGemini.assert_called_once()
    assert MockChatGemini.call_args.kwargs["model"] == settings.GEMINI_MODEL


def _provider_with_fake_model(fake_model) -> LLMProvider:
    provider = LLMProvider.__new__(LLMProvider)  # bypass __init__/build_chat_model
    provider._settings = _settings()
    provider._model = fake_model
    return provider


async def test_generate_text_returns_model_content():
    fake_model = MagicMock()
    fake_model.ainvoke = AsyncMock(return_value=MagicMock(content="hello"))
    provider = _provider_with_fake_model(fake_model)

    result = await provider.generate_text([HumanMessage(content="hi")])

    assert result == "hello"
    fake_model.ainvoke.assert_called_once()


async def test_generate_structured_uses_with_structured_output():
    class Answer(BaseModel):
        text: str

    structured_model = MagicMock()
    structured_model.ainvoke = AsyncMock(return_value=Answer(text="42"))

    fake_model = MagicMock()
    fake_model.with_structured_output.return_value = structured_model
    provider = _provider_with_fake_model(fake_model)

    result = await provider.generate_structured([HumanMessage(content="hi")], Answer)

    fake_model.with_structured_output.assert_called_once_with(Answer)
    structured_model.ainvoke.assert_called_once()
    assert result == Answer(text="42")


async def test_stream_text_yields_non_empty_chunk_content():
    async def fake_astream(messages):
        for content in ["Hel", "", "lo"]:
            yield MagicMock(content=content)

    fake_model = MagicMock()
    fake_model.astream = fake_astream
    provider = _provider_with_fake_model(fake_model)

    tokens = [token async for token in provider.stream_text([HumanMessage(content="hi")])]

    # The empty-content chunk (e.g. a provider's initial metadata-only chunk)
    # is filtered out rather than yielded as a blank token.
    assert tokens == ["Hel", "lo"]
