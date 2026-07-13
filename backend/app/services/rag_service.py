import asyncio
import uuid
from dataclasses import dataclass

from app.models.transcript import Transcript
from app.schemas.transcript import TranscriptSegment
from app.utils.chunking import chunk_transcript
from app.vector_store.chroma_client import get_video_collection
from app.vector_store.embeddings import embed_query, embed_texts

# Smaller than the ~6000-char chunks used for summarization (Step 6) —
# retrieval benefits from finer-grained chunks so a question only pulls in
# the passage that actually answers it, not a whole 6000-char block.
_RAG_CHUNK_MAX_CHARS = 1500


@dataclass
class RetrievedChunk:
    text: str
    start_seconds: float
    end_seconds: float
    distance: float


class RagService:
    """Indexes a video's transcript into ChromaDB and retrieves the chunks
    most relevant to a chat question — the retriever half of RAG.
    """

    async def ensure_indexed(self, video_id: uuid.UUID, transcript: Transcript) -> None:
        collection = await asyncio.to_thread(get_video_collection, str(video_id))
        already_indexed = await asyncio.to_thread(collection.count)
        if already_indexed > 0:
            return

        segments = [TranscriptSegment(**seg) for seg in transcript.segments]
        chunks = chunk_transcript(segments, max_chars=_RAG_CHUNK_MAX_CHARS)
        if not chunks:
            return

        texts = [chunk.text for chunk in chunks]
        embeddings = await asyncio.to_thread(embed_texts, texts)

        await asyncio.to_thread(
            collection.add,
            ids=[f"{video_id}-{i}" for i in range(len(chunks))],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {"start_seconds": chunk.start_seconds, "end_seconds": chunk.end_seconds}
                for chunk in chunks
            ],
        )

    async def retrieve_relevant_chunks(
        self, video_id: uuid.UUID, query: str, top_k: int = 5
    ) -> list[RetrievedChunk]:
        collection = await asyncio.to_thread(get_video_collection, str(video_id))
        if await asyncio.to_thread(collection.count) == 0:
            return []

        query_embedding = await asyncio.to_thread(embed_query, query)
        results = await asyncio.to_thread(
            collection.query, query_embeddings=[query_embedding], n_results=top_k
        )

        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        return [
            RetrievedChunk(
                text=doc,
                start_seconds=meta["start_seconds"],
                end_seconds=meta["end_seconds"],
                distance=dist,
            )
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]
