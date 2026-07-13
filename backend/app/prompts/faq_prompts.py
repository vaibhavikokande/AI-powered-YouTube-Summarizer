"""Prompt template for FAQ generation."""


def faq_prompt(combined_chunk_summaries: str, count: int) -> str:
    return (
        f"From the segment summaries of a video below, generate exactly {count} frequently "
        "asked questions a viewer might have after watching, each with a concise, accurate "
        "answer grounded only in the summaries below. Do not invent facts that aren't there.\n\n"
        f"Segment summaries:\n{combined_chunk_summaries}"
    )
