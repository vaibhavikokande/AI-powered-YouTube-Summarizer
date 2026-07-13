from dataclasses import dataclass

from app.schemas.transcript import TranscriptSegment


@dataclass
class TranscriptChunk:
    text: str
    start_seconds: float
    end_seconds: float


def chunk_transcript(
    segments: list[TranscriptSegment], max_chars: int = 6000
) -> list[TranscriptChunk]:
    """Group transcript segments into chunks for map-reduce summarization.

    Chunks never split a segment's text and are capped at `max_chars`
    characters — a simple, model-agnostic proxy for staying comfortably
    under any provider's context window even for multi-hour transcripts
    split into many chunks. Each chunk keeps its start/end time so
    timestamped sections can cite accurate moments later.
    """
    chunks: list[TranscriptChunk] = []
    buffer: list[str] = []
    buffer_start = 0.0
    buffer_end = 0.0
    buffer_len = 0

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue

        if buffer and buffer_len + len(text) + 1 > max_chars:
            chunks.append(
                TranscriptChunk(text=" ".join(buffer), start_seconds=buffer_start, end_seconds=buffer_end)
            )
            buffer = []
            buffer_len = 0

        if not buffer:
            buffer_start = segment.start

        buffer.append(text)
        buffer_len += len(text) + 1
        buffer_end = segment.start + segment.duration

    if buffer:
        chunks.append(
            TranscriptChunk(text=" ".join(buffer), start_seconds=buffer_start, end_seconds=buffer_end)
        )

    return chunks
