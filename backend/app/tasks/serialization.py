"""Plain-dict serializers for Celery task results.

Celery's JSON result backend can't serialize ORM objects, UUIDs, enums, or
datetimes directly — every task returns one of these dicts instead of the
model instance a synchronous service call would return.
"""

from app.models.faq import FAQItem
from app.models.flashcard import Flashcard
from app.models.note import Note
from app.models.quiz import Quiz
from app.models.summary import Summary


def summary_to_dict(summary: Summary) -> dict:
    return {
        "id": str(summary.id),
        "video_id": str(summary.video_id),
        "summary_type": summary.summary_type.value,
        "content": summary.content,
        "key_takeaways": summary.key_takeaways,
        "timestamped_sections": summary.timestamped_sections,
        "topics": summary.topics,
        "mindmap_markdown": summary.mindmap_markdown,
        "llm_provider": summary.llm_provider,
        "created_at": summary.created_at.isoformat(),
    }


def quiz_to_dict(quiz: Quiz) -> dict:
    return {
        "id": str(quiz.id),
        "title": quiz.title,
        "questions": [
            {
                "id": str(q.id),
                "question_type": q.question_type.value,
                "question_text": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
            }
            for q in quiz.questions
        ],
    }


def flashcard_to_dict(flashcard: Flashcard) -> dict:
    return {"id": str(flashcard.id), "question": flashcard.question, "answer": flashcard.answer}


def faq_item_to_dict(item: FAQItem) -> dict:
    return {
        "id": str(item.id),
        "question": item.question,
        "answer": item.answer,
        "created_at": item.created_at.isoformat(),
    }


def note_to_dict(note: Note) -> dict:
    return {
        "id": str(note.id),
        "video_id": str(note.video_id),
        "content_markdown": note.content_markdown,
        "created_at": note.created_at.isoformat(),
    }
