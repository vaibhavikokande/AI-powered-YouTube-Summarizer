from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    """Loaded once per process — the model weights are too expensive to
    reload on every request.
    """
    settings = get_settings()
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Blocking, CPU-bound — callers should run this via asyncio.to_thread."""
    model = get_embedding_model()
    return model.encode(texts).tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
