"""Prompt template for mind map generation."""


def mindmap_prompt(combined_chunk_summaries: str, video_title: str | None) -> str:
    title_line = f'Video title: "{video_title}"\n' if video_title else ""
    return (
        f"{title_line}"
        "From the segment summaries of a video below, generate a hierarchical mind map as "
        "**Markdown nested bullet points** (using '-' and two-space indentation per level, up "
        "to 3 levels deep). The root should be the video's central theme; the first level should "
        "be its main topics; deeper levels should be supporting subtopics/details. Do not include "
        "any prose outside the bullet list.\n\n"
        f"Segment summaries:\n{combined_chunk_summaries}"
    )
