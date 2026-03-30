from __future__ import annotations

from services import document_summary_service as summary_service
from services import docling_service


def _parsed_document(text: str) -> docling_service.ParsedDocument:
    return docling_service.ParsedDocument(
        filename="camera.pdf",
        text=text,
        parser_backend="docling",
        parser_mode="docling_with_legacy_fallback",
        parser_version="2.82.0",
        source_format="PDF",
        page_count=3,
        has_tables="| --- |" in text,
        has_headings="#" in text,
        structure={"headings": ["Camera", "Lens"]},
        metadata={"docling_status": "SUCCESS"},
    )


def test_generate_summary_artifacts_from_llm_json(monkeypatch):
    monkeypatch.setattr(
        summary_service,
        "get_chat_response",
        lambda **kwargs: (
            '{"summary":"Документ про устройство камеры.","key_topics":["диафрагма","экспозиция"],"suggested_questions":["Как работает диафрагма?"],"warnings":[]}',
            0.0,
        ),
    )

    artifacts = summary_service.generate_summary_artifacts(
        123,
        filename="camera.pdf",
        parsed_document=_parsed_document("# Camera\n\nCamera text.\n"),
    )

    assert artifacts.status == "generated"
    assert artifacts.source == "llm"
    assert artifacts.summary == "Документ про устройство камеры."
    assert artifacts.key_topics == ["диафрагма", "экспозиция"]
    assert artifacts.suggested_questions == ["Как работает диафрагма?"]


def test_generate_summary_artifacts_falls_back_on_invalid_json(monkeypatch):
    monkeypatch.setattr(
        summary_service,
        "get_chat_response",
        lambda **kwargs: ("not a json response", 0.0),
    )

    artifacts = summary_service.generate_summary_artifacts(
        123,
        filename="camera.pdf",
        parsed_document=_parsed_document("# Camera\n\nCamera text.\n"),
    )

    assert artifacts.status == "fallback_preview"
    assert artifacts.source == "fallback"
    assert "локальный preview" in artifacts.warnings[0]
    assert artifacts.error is not None


def test_generate_summary_artifacts_falls_back_on_empty_digest(monkeypatch):
    monkeypatch.setattr(summary_service, "get_chat_response", lambda **kwargs: ("{}", 0.0))

    artifacts = summary_service.generate_summary_artifacts(
        123,
        filename="empty.pdf",
        parsed_document=docling_service.ParsedDocument(
            filename="empty.pdf",
            text="   ",
            parser_backend="docling",
            parser_mode="docling_with_legacy_fallback",
            parser_version="2.82.0",
            source_format="PDF",
            structure={},
            metadata={"docling_status": "SUCCESS"},
        ),
    )

    assert artifacts.status == "fallback_preview"
    assert artifacts.summary
    assert artifacts.error == "Пустой document digest для summary."


def test_format_summary_preview_html_contains_sections():
    html_preview = summary_service.format_summary_preview_html(
        summary_service.SummaryArtifacts(
            summary="Краткое резюме документа.",
            key_topics=["Тема 1", "Тема 2"],
            suggested_questions=["Что сказано про тему 1?"],
            warnings=["Fallback preview"],
        )
    )

    assert html_preview is not None
    assert "<b>Краткое резюме</b>" in html_preview
    assert "Тема 1" in html_preview
    assert "Что сказано про тему 1?" in html_preview
