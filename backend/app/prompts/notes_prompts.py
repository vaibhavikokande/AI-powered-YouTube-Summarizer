"""Prompt template for clean notes generation."""


def notes_prompt(combined_chunk_summaries: str, video_title: str | None) -> str:
    title_line = f'Video title: "{video_title}"\n' if video_title else ""
    return (
        f"{title_line}"
        "From the segment summaries of a video below, write clean, well-organized study notes "
        "in Markdown: use headings (##) for major sections, bullet points for individual facts "
        "or ideas, and **bold** for key terms. Only include information present in the summaries "
        "below.\n\n"
        f"Segment summaries:\n{combined_chunk_summaries}"
    )
