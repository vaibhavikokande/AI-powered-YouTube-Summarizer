from functools import lru_cache

import chromadb

from app.core.config import get_settings


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    settings = get_settings()
    if settings.VECTOR_STORE_PROVIDER != "chroma":
        raise NotImplementedError(
            f"VECTOR_STORE_PROVIDER={settings.VECTOR_STORE_PROVIDER!r} is not yet supported "
            "— only 'chroma' is implemented."
        )
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def get_video_collection(video_id: str) -> chromadb.Collection:
    """One collection per video, namespaced by id, so chat retrieval never
    crosses between videos.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(name=f"video_{video_id}")
