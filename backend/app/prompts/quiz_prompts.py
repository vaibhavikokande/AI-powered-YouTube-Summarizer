"""Prompt template for quiz generation."""

from app.models.enums import QuizQuestionType

_TYPE_LABELS = {
    QuizQuestionType.MCQ: "multiple-choice (4 options in `options`, exactly one correct)",
    QuizQuestionType.TRUE_FALSE: "true/false (`options` must be null; `correct_answer` is 'True' or 'False')",
    QuizQuestionType.FILL_BLANK: "fill-in-the-blank (`question_text` contains a blank as '____'; "
    "`options` must be null)",
}


def quiz_prompt(
    combined_chunk_summaries: str, question_types: list[QuizQuestionType], count: int
) -> str:
    allowed = ", ".join(f"{qt.value} ({_TYPE_LABELS[qt]})" for qt in question_types)
    return (
        f"From the segment summaries of a video below, generate a quiz titled after the video's "
        f"main topic, with exactly {count} questions total, drawn only from these allowed "
        f"question types: {allowed}. Distribute questions roughly evenly across the allowed "
        "types. Every question and its correct_answer must be verifiable from the summaries "
        "below — never invent facts.\n\n"
        f"Segment summaries:\n{combined_chunk_summaries}"
    )
