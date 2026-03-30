"""
Document summary artifacts for KB uploads.

Sprint 4 scope:
- build a compact digest from a parsed/normalized document
- ask the selected LLM for strict JSON output
- fall back to a local preview when LLM is unavailable or returns bad JSON
- provide a Telegram-friendly HTML preview string
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
import html
import json
import logging
import re
from typing import Any

import services.kb_ingestion_pipeline as kb_ingest_svc
from services.config_registry import get_setting
from user_storage import get_user_model
from utils import get_chat_response

logger = logging.getLogger("blabber")

MAX_HEADINGS = 8
MAX_PROSE_BLOCKS = 4
MAX_TABLE_BLOCKS = 2
MAX_BLOCK_CHARS = 500
MAX_SUMMARY_LEN = 700

SUMMARY_SYSTEM_PROMPT = """
Ты анализируешь документ для Telegram-бота и должен вернуть ТОЛЬКО валидный JSON.

Формат JSON строго такой:
{
  "summary": "<расширенное, но компактное резюме документа на русском, 3-6 предложений>",
  "key_topics": ["<тема 1>", "<тема 2>", "<тема 3>"],
  "suggested_questions": ["<пример вопроса 1>", "<пример вопроса 2>", "<пример вопроса 3>"],
  "warnings": ["<необязательное предупреждение 1>"]
}

Правила:
- отвечай только JSON, без markdown и без пояснений вокруг
- summary должен быть полезным и конкретным
- key_topics: 3-7 коротких тем
- suggested_questions: 3-6 практичных вопросов, которые пользователь может задать по документу
- если данные слабые или документ разобран частично, добавь warnings
"""


@dataclass
class SummaryArtifacts:
    summary: str
    key_topics: list[str] = field(default_factory=list)
    suggested_questions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    status: str = "generated"
    source: str = "llm"
    model: str | None = None
    generated_at: str | None = None
    error: str | None = None
    digest: dict[str, Any] = field(default_factory=dict)


def _clip(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _parse_llm_json(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Не удалось распарсить JSON из ответа LLM: {raw[:200]}")


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def resolve_summary_model(telegram_id: int) -> str:
    configured = get_setting("kb_doc_summary_model", None, env_key="KB_DOC_SUMMARY_MODEL")
    if configured:
        return str(configured).strip()
    return get_user_model(telegram_id) or "openrouter"


def build_document_digest(
    *,
    filename: str,
    parsed_document: Any,
) -> dict[str, Any]:
    normalized = kb_ingest_svc.normalize_document(
        filename=filename,
        text=parsed_document.text,
        parser_backend=parsed_document.parser_backend,
        source_format=parsed_document.source_format,
        structure=parsed_document.structure,
        metadata=parsed_document.metadata,
    )
    chunk_preview = kb_ingest_svc.build_chunks(normalized)
    stats = kb_ingest_svc.summarize_document_structure(normalized, chunk_preview)

    prose_previews = [
        _clip(block.text, MAX_BLOCK_CHARS)
        for block in normalized.blocks
        if not block.is_table and block.text.strip()
    ][:MAX_PROSE_BLOCKS]

    table_previews = [
        _clip(block.text, MAX_BLOCK_CHARS)
        for block in normalized.blocks
        if block.is_table and block.text.strip()
    ][:MAX_TABLE_BLOCKS]

    headings = list((parsed_document.structure or {}).get("headings") or [])[:MAX_HEADINGS]
    return {
        "title": filename,
        "parser_backend": parsed_document.parser_backend,
        "source_format": parsed_document.source_format,
        "page_count": parsed_document.page_count,
        "headings": headings,
        "prose_preview": prose_previews,
        "table_preview": table_previews,
        "structure_stats": {
            **stats,
            "has_tables": bool(parsed_document.has_tables),
            "has_headings": bool(parsed_document.has_headings),
        },
        "warnings": list(parsed_document.warnings or []),
        "fallback_used": bool(parsed_document.fallback_used),
    }


def _coerce_artifacts(data: dict[str, Any]) -> SummaryArtifacts:
    summary = _clip(str(data.get("summary") or "").strip(), MAX_SUMMARY_LEN)
    key_topics = [
        _clip(str(item).strip(), 120)
        for item in (data.get("key_topics") or [])
        if str(item).strip()
    ][:7]
    suggested_questions = [
        _clip(str(item).strip(), 180)
        for item in (data.get("suggested_questions") or [])
        if str(item).strip()
    ][:6]
    warnings = [
        _clip(str(item).strip(), 180)
        for item in (data.get("warnings") or [])
        if str(item).strip()
    ][:5]
    return SummaryArtifacts(
        summary=summary,
        key_topics=key_topics,
        suggested_questions=suggested_questions,
        warnings=warnings,
        generated_at=_now_iso(),
    )


def _build_fallback_artifacts(*, digest: dict[str, Any], error: str | None = None) -> SummaryArtifacts:
    prose_preview = list(digest.get("prose_preview") or [])
    headings = [str(item).strip() for item in (digest.get("headings") or []) if str(item).strip()]
    stats = dict(digest.get("structure_stats") or {})

    summary_parts: list[str] = []
    if headings:
        summary_parts.append(f"Документ охватывает разделы: {', '.join(headings[:4])}.")
    if prose_preview:
        summary_parts.append(_clip(prose_preview[0], 280))
    if stats:
        stat_bits: list[str] = []
        if stats.get("block_count"):
            stat_bits.append(f"блоков: {int(stats['block_count'])}")
        if stats.get("table_count"):
            stat_bits.append(f"таблиц: {int(stats['table_count'])}")
        if stats.get("chunk_count"):
            stat_bits.append(f"чанков: {int(stats['chunk_count'])}")
        if stat_bits:
            summary_parts.append("Структура документа: " + ", ".join(stat_bits) + ".")

    topics = headings[:5]
    if not topics and prose_preview:
        topics = [_clip(line, 60) for line in prose_preview[:3]]

    questions = [f"Что сказано в документе про {topic}?" for topic in topics[:3] if topic]
    if not questions:
        questions = [
            "Какое основное содержание документа?",
            "Какие ключевые темы описаны в документе?",
            "Какие выводы можно сделать по документу?",
        ]

    warnings = ["Показан локальный preview без LLM-обобщения."]
    if error:
        warnings.append(_clip(error, 180))

    return SummaryArtifacts(
        summary=_clip(" ".join(summary_parts).strip() or "Документ успешно разобран, но LLM-summary недоступно.", MAX_SUMMARY_LEN),
        key_topics=topics[:5],
        suggested_questions=questions[:5],
        warnings=warnings,
        status="fallback_preview",
        source="fallback",
        generated_at=_now_iso(),
        error=error,
        digest=digest,
    )


def generate_summary_artifacts(
    telegram_id: int,
    *,
    filename: str,
    parsed_document: Any,
    model: str | None = None,
) -> SummaryArtifacts:
    digest = build_document_digest(filename=filename, parsed_document=parsed_document)
    if not (digest.get("prose_preview") or digest.get("table_preview") or digest.get("headings")):
        return _build_fallback_artifacts(digest=digest, error="Пустой document digest для summary.")

    resolved_model = model or resolve_summary_model(telegram_id)
    user_message = json.dumps(digest, ensure_ascii=False, indent=2)

    logger.info(
        "kb_doc_summary_started",
        extra={
            "event": "kb_doc_summary_started",
            "telegram_id": telegram_id,
            "model": resolved_model,
            "digest_size": len(user_message),
        },
    )
    try:
        raw_response, _ = get_chat_response(
            user_message=user_message,
            model=resolved_model,
            system_message=SUMMARY_SYSTEM_PROMPT,
            telegram_id=telegram_id,
        )
        artifacts = _coerce_artifacts(_parse_llm_json(raw_response))
        if not artifacts.summary:
            raise ValueError("LLM summary вернул пустое поле summary")
        artifacts.model = resolved_model
        artifacts.source = "llm"
        artifacts.status = "generated"
        artifacts.digest = digest
        logger.info(
            "kb_doc_summary_finished",
            extra={
                "event": "kb_doc_summary_finished",
                "telegram_id": telegram_id,
                "status": artifacts.status,
                "topics": len(artifacts.key_topics),
                "questions": len(artifacts.suggested_questions),
            },
        )
        return artifacts
    except Exception as exc:
        logger.warning(
            "kb_doc_summary_failed",
            extra={
                "event": "kb_doc_summary_failed",
                "telegram_id": telegram_id,
                "model": resolved_model,
                "error": str(exc)[:200],
            },
        )
        fallback = _build_fallback_artifacts(digest=digest, error=str(exc))
        fallback.model = resolved_model
        return fallback


def format_summary_preview_html(artifacts: SummaryArtifacts) -> str | None:
    if not artifacts.summary:
        return None

    parts = [
        "<b>Краткое резюме</b>",
        html.escape(artifacts.summary),
    ]
    if artifacts.key_topics:
        parts.append("<b>Ключевые темы</b>")
        parts.extend(f"• {html.escape(topic)}" for topic in artifacts.key_topics[:5])
    if artifacts.suggested_questions:
        parts.append("<b>Что теперь можно спросить</b>")
        parts.extend(f"• {html.escape(question)}" for question in artifacts.suggested_questions[:4])
    if artifacts.warnings:
        parts.append("<b>Примечание</b>")
        parts.extend(f"• {html.escape(item)}" for item in artifacts.warnings[:2])
    return "\n".join(parts)
