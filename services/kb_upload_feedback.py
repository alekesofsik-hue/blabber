"""
Telegram-friendly KB upload/review formatting helpers.
"""

from __future__ import annotations

import html
from typing import Any

from services.document_summary_service import SummaryArtifacts

MAX_TELEGRAM_HTML_CHARS = 3800


def _truncate_html_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _format_parser_note(parsed_document: Any) -> list[str]:
    notes: list[str] = []
    if parsed_document is None:
        return notes

    parser_backend = getattr(parsed_document, "parser_backend", None)
    parser_label = "Docling" if parser_backend == "docling" else "legacy parser"
    notes.append(f"Парсер: <b>{html.escape(parser_label)}</b>")

    if getattr(parsed_document, "fallback_used", False):
        notes.append("Документ загружен через fallback parser, поэтому структура могла сохраниться не полностью.")
    elif getattr(parsed_document, "warnings", None):
        notes.append("Документ разобран частично: некоторые элементы могли сохраниться неидеально.")

    if getattr(parsed_document, "has_tables", False):
        notes.append("Таблицы тоже учтены в базе знаний.")
    if getattr(parsed_document, "has_headings", False):
        notes.append("Структура разделов сохранена и будет полезна для поиска.")
    return notes


def _format_summary_section(summary_artifacts: SummaryArtifacts | None) -> list[str]:
    if summary_artifacts is None:
        return []

    parts: list[str] = []
    if summary_artifacts.summary:
        parts.append("<b>Краткое резюме</b>")
        parts.append(html.escape(summary_artifacts.summary))

    if summary_artifacts.key_topics:
        parts.append("<b>Ключевые темы</b>")
        parts.extend(f"• {html.escape(topic)}" for topic in summary_artifacts.key_topics[:5])

    if summary_artifacts.suggested_questions:
        parts.append("<b>Что теперь можно спросить</b>")
        parts.extend(f"• {html.escape(question)}" for question in summary_artifacts.suggested_questions[:4])

    if summary_artifacts.status != "generated":
        parts.append("<b>Примечание</b>")
        parts.append("Показан упрощённый preview документа, потому что авто-summary собрано не полностью.")
    elif summary_artifacts.warnings:
        parts.append("<b>Примечание</b>")
        parts.extend(f"• {html.escape(item)}" for item in summary_artifacts.warnings[:2])

    return parts


def build_upload_success_html(
    *,
    filename: str,
    index_result_message: str,
    parsed_document: Any | None = None,
    summary_artifacts: SummaryArtifacts | None = None,
    kb_auto_enabled: bool = False,
) -> str:
    parts = [
        f"✅ <b>{html.escape(filename)}</b> добавлен в базу знаний!",
        f"📄 {index_result_message}",
    ]

    parser_notes = _format_parser_note(parsed_document)
    if parser_notes:
        parts.append("<b>Что учтено при загрузке</b>")
        parts.extend(f"• {html.escape(note) if '<b>' not in note else note}" for note in parser_notes)

    summary_parts = _format_summary_section(summary_artifacts)
    if summary_parts:
        parts.append("")
        parts.extend(summary_parts)

    parts.append("")
    parts.append("<b>Что можно сделать дальше</b>")
    parts.append("• Задай вопрос по документу своими словами.")
    parts.append("• Спроси про конкретный раздел, правило или таблицу.")
    parts.append("• Открой <code>/kb</code>, чтобы посмотреть статус документов.")

    if kb_auto_enabled:
        parts.append("")
        parts.append("✅ База знаний автоматически включена.")

    message = "\n".join(part for part in parts if part is not None)
    return _truncate_html_text(message, MAX_TELEGRAM_HTML_CHARS)
