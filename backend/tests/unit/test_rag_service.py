import uuid
from unittest.mock import MagicMock, patch

from app.services.rag_service import RagService, RetrievedChunk


def _mock_collection(count_value: int = 0) -> MagicMock:
    collection = MagicMock()
    collection.count.return_value = count_value
    return collection


async def test_ensure_indexed_skips_when_already_indexed():
    collection = _mock_collection(count_value=5)

    with (
        patch("app.services.rag_service.get_video_collection", return_value=collection),
        patch("app.services.rag_service.embed_texts") as mock_embed,
    ):
        await RagService().ensure_indexed(uuid.uuid4(), MagicMock(segments=[]))

    mock_embed.assert_not_called()
    collection.add.assert_not_called()


async def test_ensure_indexed_embeds_and_adds_when_empty():
    collection = _mock_collection(count_value=0)
    transcript = MagicMock()
    transcript.segments = [{"start": 0.0, "duration": 2.0, "text": "hello world"}]

    with (
        patch("app.services.rag_service.get_video_collection", return_value=collection),
        patch("app.services.rag_service.embed_texts", return_value=[[0.1, 0.2]]) as mock_embed,
    ):
        await RagService().ensure_indexed(uuid.uuid4(), transcript)

    mock_embed.assert_called_once()
    collection.add.assert_called_once()
    _, kwargs = collection.add.call_args
    assert kwargs["documents"] == ["hello world"]
    assert kwargs["embeddings"] == [[0.1, 0.2]]
    assert kwargs["metadatas"] == [{"start_seconds": 0.0, "end_seconds": 2.0}]


async def test_retrieve_relevant_chunks_returns_empty_when_not_indexed():
    collection = _mock_collection(count_value=0)

    with patch("app.services.rag_service.get_video_collection", return_value=collection):
        result = await RagService().retrieve_relevant_chunks(uuid.uuid4(), "question")

    assert result == []
    collection.query.assert_not_called()


async def test_retrieve_relevant_chunks_maps_query_results():
    collection = _mock_collection(count_value=3)
    collection.query.return_value = {
        "documents": [["hello world"]],
        "metadatas": [[{"start_seconds": 0.0, "end_seconds": 2.0}]],
        "distances": [[0.1234]],
    }

    with (
        patch("app.services.rag_service.get_video_collection", return_value=collection),
        patch("app.services.rag_service.embed_query", return_value=[0.1, 0.2]),
    ):
        result = await RagService().retrieve_relevant_chunks(uuid.uuid4(), "question")

    assert result == [
        RetrievedChunk(text="hello world", start_seconds=0.0, end_seconds=2.0, distance=0.1234)
    ]
