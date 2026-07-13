"""Prompt templates for the summarization pipeline.

Kept separate from `summarization_service.py` per `docs/SPEC.md`'s prompt
engineering guidelines: every prompt is a named function here, never
inlined in a service.
"""

from app.models.enums import SummaryType

_SUMMARY_TYPE_INSTRUCTIONS = {
    SummaryType.SHORT: "Write a single, tight paragraph (3-4 sentences) capturing only the core message.",
    SummaryType.MEDIUM: "Write 2-3 paragraphs covering the main points and how they connect.",
    SummaryType.DETAILED: (
        "Write a thorough, well-organized summary covering all major points, supporting "
        "arguments, and examples discussed. Use multiple paragraphs."
    ),
    SummaryType.BULLET: (
        "Write the summary as a bulleted list (using '- ') of the key points, one point per "
        "line, ordered as they were discussed."
    ),
}


def chunk_summary_prompt(chunk_text: str) -> str:
    """Map step: summarize one transcript chunk in isolation."""
    return (
        "You are summarizing one segment of a longer video transcript. Summarize only what is "
        "in this segment, concisely and factually. Do not add information that isn't in the "
        "text. Do not reference 'this segment' or 'the transcript' — write as if summarizing "
        "the content directly.\n\n"
        f"Segment:\n{chunk_text}"
    )


def reduce_summary_prompt(
    combined_chunk_summaries: str, summary_type: SummaryType, video_title: str | None
) -> str:
    """Reduce step: combine chunk summaries into one final summary of the requested length/style."""
    instruction = _SUMMARY_TYPE_INSTRUCTIONS[summary_type]
    title_line = f'Video title: "{video_title}"\n' if video_title else ""
    return (
        f"{title_line}"
        "Below are chronological summaries of consecutive segments of a video's transcript. "
        f"Combine them into a single, coherent summary of the whole video.\n\n{instruction}\n\n"
        "Only use information present in the segment summaries below — never invent facts, "
        "names, or figures that aren't there.\n\n"
        f"Segment summaries:\n{combined_chunk_summaries}"
    )


def key_takeaways_prompt(combined_chunk_summaries: str) -> str:
    return (
        "From the segment summaries of a video below, extract:\n"
        "- important_concepts: key ideas or concepts explained\n"
        "- action_items: concrete actions or recommendations the speaker suggests taking\n"
        "- important_quotes: notable verbatim-style quotes or statements (only if clearly present)\n"
        "- definitions: term -> definition, for any terms explicitly defined\n"
        "- statistics: any numbers, percentages, or statistics mentioned, with brief context\n\n"
        "If a category has nothing relevant, return an empty list/object for it — never invent "
        "content to fill a category.\n\n"
        f"Segment summaries:\n{combined_chunk_summaries}"
    )


def topics_prompt(combined_chunk_summaries: str) -> str:
    return (
        "From the segment summaries of a video below, extract:\n"
        "- main_topics: the handful of primary topics covered\n"
        "- subtopics: more specific subtopics within those\n"
        "- tags: short, lowercase, hyphenated tags suitable for search/filtering\n\n"
        f"Segment summaries:\n{combined_chunk_summaries}"
    )


def timestamped_sections_prompt(timestamped_chunk_summaries: list[tuple[float, str]]) -> str:
    """`timestamped_chunk_summaries` is a list of (start_seconds, chunk_summary) pairs, in order."""
    formatted = "\n\n".join(f"[{int(start)}s] {summary}" for start, summary in timestamped_chunk_summaries)
    return (
        "Below are timestamped summaries of consecutive segments of a video, in chronological "
        "order. Group them into logical sections (e.g. Introduction, a specific subtopic, Demo, "
        "Conclusion) — merging adjacent segments that belong to the same section. For each "
        "section, return its start timestamp in whole seconds (use the timestamp of the first "
        "segment in that section), a short title (2-6 words), and a 1-3 sentence summary.\n\n"
        f"Segments:\n{formatted}"
    )
