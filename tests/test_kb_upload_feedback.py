from __future__ import annotations

from services.document_summary_service import SummaryArtifacts
from services.kb_upload_feedback import build_upload_success_html


class _Parsed:
    parser_backend = "docling"
    fallback_used = False
    warnings = []
    has_tables = True
    has_headings = True


def test_build_upload_success_html_renders_card_sections():
    message = build_upload_success_html(
        filename="camera.pdf",
        index_result_message="Проиндексировано 12 фрагментов + embeddings",
        parsed_document=_Parsed(),
        summary_artifacts=SummaryArtifacts(
            summary="Документ описывает устройство камеры.",
            key_topics=["диафрагма", "объектив"],
            suggested_questions=["Как работает диафрагма?"],
            status="generated",
        ),
        kb_auto_enabled=True,
    )

    assert "✅ <b>camera.pdf</b> добавлен в базу знаний!" in message
    assert "<b>Что учтено при загрузке</b>" in message
    assert "Таблицы тоже учтены" in message
    assert "<b>Краткое резюме</b>" in message
    assert "<b>Что теперь можно спросить</b>" in message
    assert "✅ База знаний автоматически включена." in message


def test_build_upload_success_html_shows_partial_success_note():
    parsed = _Parsed()
    parsed.fallback_used = True
    parsed.warnings = ["partial parse"]

    message = build_upload_success_html(
        filename="fallback.pdf",
        index_result_message="Проиндексировано 8 фрагментов (BM25-only, embedding request failed)",
        parsed_document=parsed,
        summary_artifacts=SummaryArtifacts(
            summary="Показан локальный preview.",
            key_topics=["камера"],
            suggested_questions=["Что сказано про камеру?"],
            status="fallback_preview",
        ),
    )

    assert "fallback parser" in message
    assert "упрощённый preview документа" in message
    assert "embedding request failed" in message
