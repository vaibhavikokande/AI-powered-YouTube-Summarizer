from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    import chromadb


# chromadb (and its compiled hnswlib dependency) is only needed for the RAG
# chat feature. Importing it lazily, rather than at module scope, means an
# environment missing that one optional dependency loses chat but keeps the
# rest of the API (auth, history, summarization, ...) working.
@lru_cache
def get_chroma_client() -> "chromadb.ClientAPI":
    settings = get_settings()
    if settings.VECTOR_STORE_PROVIDER != "chroma":
        raise NotImplementedError(
            f"VECTOR_STORE_PROVIDER={settings.VECTOR_STORE_PROVIDER!r} is not yet supported "
            "— only 'chroma' is implemented."
        )
    import chromadb

    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def get_video_collection(video_id: str) -> "chromadb.Collection":
    """One collection per video, namespaced by id, so chat retrieval never
    crosses between videos.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(name=f"video_{video_id}")
