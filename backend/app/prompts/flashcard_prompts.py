"""Prompt template for flashcard generation."""


def flashcard_prompt(combined_chunk_summaries: str, count: int) -> str:
    return (
        f"From the segment summaries of a video below, generate exactly {count} study "
        "flashcards. Each flashcard's question should test recall or understanding of one "
        "specific fact, concept, or definition from the video; the answer should be concise "
        "(1-2 sentences) and correct based only on the summaries below.\n\n"
        f"Segment summaries:\n{combined_chunk_summaries}"
    )
