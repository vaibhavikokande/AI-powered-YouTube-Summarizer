import io
import uuid

import pytest
from docx import Document

from app.core.exceptions import ValidationAppError
from app.models.enums import SummaryType
from app.models.summary import Summary
from app.services.export_service import ExportService


def _sample_summary() -> Summary:
    return Summary(
        id=uuid.uuid4(),
        video_id=uuid.uuid4(),
        summary_type=SummaryType.MEDIUM,
        content="This video explains how transformers work in NLP.",
        key_takeaways={
            "important_concepts": ["Attention mechanism"],
            "action_items": ["Read the original paper"],
            "important_quotes": ["Attention is all you need"],
            "definitions": {},
            "statistics": ["Trained on 8 GPUs for 3.5 days"],
        },
        timestamped_sections=[
            {"timestamp_seconds": 0, "title": "Intro", "summary": "Introduction to the topic"}
        ],
        topics={"main_topics": ["NLP", "Transformers"], "subtopics": [], "tags": ["ai", "nlp"]},
        mindmap_markdown="- Transformers\n  - Attention",
        llm_provider="claude",
    )


def test_export_markdown_contains_expected_sections():
    result = ExportService().export(_sample_summary(), "My Video", "markdown")

    assert result.media_type == "text/markdown"
    assert result.filename == "My_Video.md"
    text = result.content.decode("utf-8")
    assert "# My Video" in text
    assert "Attention mechanism" in text
    assert "## Topics" in text


def test_export_txt_contains_expected_sections():
    result = ExportService().export(_sample_summary(), "My Video", "txt")

    assert result.media_type == "text/plain"
    text = result.content.decode("utf-8")
    assert "My Video" in text
    assert "TOPICS" in text
    assert "Attention mechanism" in text


def test_export_docx_produces_valid_document():
    result = ExportService().export(_sample_summary(), "My Video", "docx")

    assert result.media_type.endswith("wordprocessingml.document")
    document = Document(io.BytesIO(result.content))
    full_text = "\n".join(p.text for p in document.paragraphs)
    assert "Attention mechanism" in full_text


def test_export_pdf_produces_valid_pdf_bytes():
    result = ExportService().export(_sample_summary(), "My Video", "pdf")

    assert result.media_type == "application/pdf"
    assert result.content.startswith(b"%PDF")


def test_export_pdf_escapes_special_characters_without_raising():
    summary = _sample_summary()
    summary.content = "A & B < C > D"

    result = ExportService().export(summary, "My Video", "pdf")

    assert result.content.startswith(b"%PDF")


def test_export_rejects_unsupported_format():
    with pytest.raises(ValidationAppError):
        ExportService().export(_sample_summary(), "My Video", "epub")
