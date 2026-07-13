import uuid
from unittest.mock import AsyncMock, MagicMock

from app.models.enums import QuizQuestionType
from app.schemas.quiz import QuizGenerationResult, QuizQuestionPair
from app.services.quiz_service import QuizService


def _service_with_mocks() -> QuizService:
    llm = MagicMock()
    llm.generate_structured = AsyncMock(
        return_value=QuizGenerationResult(
            title="Test Quiz",
            questions=[
                QuizQuestionPair(
                    question_type=QuizQuestionType.MCQ,
                    question_text="What is X?",
                    options=["A", "B", "C", "D"],
                    correct_answer="A",
                )
            ],
        )
    )

    content_prep = MagicMock()
    content_prep.get_combined_summary = AsyncMock(return_value="combined summary")

    service = QuizService(session=MagicMock(), llm_provider=llm, content_prep=content_prep)
    service._repository = MagicMock()
    return service


def _fake_video():
    video = MagicMock()
    video.id = uuid.uuid4()
    return video


async def test_generate_returns_existing_quiz_without_llm_call():
    service = _service_with_mocks()
    existing = MagicMock()
    service._repository.get_by_video = AsyncMock(return_value=existing)

    result = await service.generate(_fake_video(), MagicMock(), question_types=[QuizQuestionType.MCQ])

    assert result is existing
    service._llm.generate_structured.assert_not_called()


async def test_generate_creates_quiz_when_none_exists():
    service = _service_with_mocks()
    service._repository.get_by_video = AsyncMock(return_value=None)
    service._repository.create = AsyncMock(return_value="persisted quiz")

    result = await service.generate(
        _fake_video(), MagicMock(), question_types=[QuizQuestionType.MCQ], count=1
    )

    assert result == "persisted quiz"
    video_id, title, questions = service._repository.create.call_args.args
    assert title == "Test Quiz"
    assert len(questions) == 1
