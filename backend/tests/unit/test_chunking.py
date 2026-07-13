from app.schemas.transcript import TranscriptSegment
from app.utils.chunking import chunk_transcript


def _segment(start: float, duration: float, text: str) -> TranscriptSegment:
    return TranscriptSegment(start=start, duration=duration, text=text)


def test_empty_segments_produce_no_chunks():
    assert chunk_transcript([]) == []


def test_single_segment_produces_one_chunk_with_matching_times():
    segments = [_segment(0.0, 2.5, "Hello world")]

    chunks = chunk_transcript(segments)

    assert len(chunks) == 1
    assert chunks[0].text == "Hello world"
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 2.5


def test_small_segments_merge_into_a_single_chunk():
    segments = [
        _segment(0.0, 1.0, "One."),
        _segment(1.0, 1.0, "Two."),
        _segment(2.0, 1.0, "Three."),
    ]

    chunks = chunk_transcript(segments, max_chars=1000)

    assert len(chunks) == 1
    assert chunks[0].text == "One. Two. Three."
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 3.0


def test_segments_split_into_multiple_chunks_when_exceeding_max_chars():
    segments = [
        _segment(0.0, 1.0, "a" * 10),
        _segment(1.0, 1.0, "b" * 10),
        _segment(2.0, 1.0, "c" * 10),
    ]

    chunks = chunk_transcript(segments, max_chars=15)

    assert len(chunks) == 3
    assert chunks[0].text == "a" * 10
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 1.0
    assert chunks[1].text == "b" * 10
    assert chunks[1].start_seconds == 1.0
    assert chunks[2].text == "c" * 10
    assert chunks[2].start_seconds == 2.0
    assert chunks[2].end_seconds == 3.0


def test_whitespace_only_segments_are_skipped():
    segments = [
        _segment(0.0, 1.0, "Hello"),
        _segment(1.0, 1.0, "   "),
        _segment(2.0, 1.0, "world"),
    ]

    chunks = chunk_transcript(segments, max_chars=1000)

    assert len(chunks) == 1
    assert chunks[0].text == "Hello world"
