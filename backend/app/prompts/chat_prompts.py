"""Prompt templates for the RAG chat feature."""


def rag_system_prompt(video_title: str | None) -> str:
    title = f' titled "{video_title}"' if video_title else ""
    return (
        f"You are answering questions about a YouTube video{title}, based only on the "
        "transcript excerpts provided below. If the answer isn't in the excerpts, say so "
        "plainly — never guess or fall back on outside knowledge the video didn't state."
    )


def rag_context_block(chunks: list[tuple[float, str]]) -> str:
    """`chunks` is a list of (start_seconds, text) pairs from the retriever."""
    if not chunks:
        return "No relevant transcript excerpts were found for this question."

    formatted = "\n\n".join(f"[{_format_timestamp(start)}] {text}" for start, text in chunks)
    return f"Relevant transcript excerpts:\n{formatted}"


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
