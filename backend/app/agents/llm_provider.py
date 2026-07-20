"""Provider-agnostic LLM client.

Every service that needs an LLM (summarization, quiz/flashcard/FAQ
generation, RAG chat) goes through `LLMProvider` instead of importing
`langchain_anthropic`/`langchain_openai`/`langchain_google_genai` directly.
`LLM_PROVIDER` in settings selects which one backs it at runtime, so
switching providers is a one-line env var change, not a code change.
"""

import logging
from collections.abc import AsyncIterator
from typing import TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def _collect_transient_exception_types() -> tuple[type[Exception], ...]:
    """Each provider SDK's rate-limit/timeout/connection error types.

    Collected lazily via try/except rather than importing at module scope,
    so this module still imports cleanly in a deployment that only installs
    one provider's SDK.
    """
    types: list[type[Exception]] = []

    try:
        import anthropic

        types += [anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError]
    except ImportError:
        pass

    try:
        import openai

        types += [openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError]
    except ImportError:
        pass

    try:
        from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

        types += [ResourceExhausted, ServiceUnavailable]
    except ImportError:
        pass

    return tuple(types)


_TRANSIENT_EXCEPTIONS = _collect_transient_exception_types()


def build_chat_model(settings: Settings | None = None, *, temperature: float = 0.2) -> BaseChatModel:
    """Construct the LangChain chat model for whichever provider LLM_PROVIDER selects."""
    settings = settings or get_settings()
    provider = settings.LLM_PROVIDER

    if provider == "claude":
        from langchain_anthropic import ChatAnthropic

        if not settings.ANTHROPIC_API_KEY:
            raise ExternalServiceError("ANTHROPIC_API_KEY is not configured.")
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=temperature,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.OPENAI_API_KEY:
            raise ExternalServiceError("OPENAI_API_KEY is not configured.")
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
        )
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.GOOGLE_API_KEY:
            raise ExternalServiceError("GOOGLE_API_KEY is not configured.")
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
        )
    else:
        # settings.LLM_PROVIDER is a Literal["claude", "openai", "gemini",
        # "openrouter"], so this is the only remaining case. OpenRouter
        # speaks the OpenAI API shape, so ChatOpenAI works unmodified —
        # it just needs pointing at OpenRouter's base URL instead of
        # OpenAI's.
        from langchain_openai import ChatOpenAI

        if not settings.OPENROUTER_API_KEY:
            raise ExternalServiceError("OPENROUTER_API_KEY is not configured.")
        return ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
        )


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(_TRANSIENT_EXCEPTIONS),
)
async def _ainvoke_with_retry(model, messages: list[BaseMessage]):
    return await model.ainvoke(messages)


class LLMProvider:
    """Thin facade over a LangChain chat model: retries transient failures
    and hides the difference between plain text and structured-output calls.
    """

    def __init__(self, settings: Settings | None = None, *, temperature: float = 0.2):
        self._settings = settings or get_settings()
        self._model = build_chat_model(self._settings, temperature=temperature)

    @property
    def provider_name(self) -> str:
        return self._settings.LLM_PROVIDER

    async def generate_text(self, messages: list[BaseMessage]) -> str:
        response = await _ainvoke_with_retry(self._model, messages)
        return response.content

    async def generate_structured(
        self, messages: list[BaseMessage], schema: type[SchemaT]
    ) -> SchemaT:
        """Return the LLM's response parsed directly into `schema`.

        Uses each provider's native structured-output/JSON mode (via
        LangChain's `with_structured_output`) so callers get a validated
        Pydantic object instead of hand-parsing JSON out of free text.
        """
        structured_model = self._model.with_structured_output(schema)
        return await _ainvoke_with_retry(structured_model, messages)

    async def stream_text(self, messages: list[BaseMessage]) -> AsyncIterator[str]:
        """Yield answer tokens as they arrive, for chat's streamed responses.

        Deliberately not wrapped in the retry logic above: once tokens have
        started reaching the client, retrying the whole call would duplicate
        output rather than recover cleanly.
        """
        async for chunk in self._model.astream(messages):
            if chunk.content:
                yield chunk.content
