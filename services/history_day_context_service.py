"""
Saved-context retrieval and prompt injection for the History Day scenario.

This layer is intentionally separate from:
- the short-lived `context_service`
- KB retrieval
- the low-level LanceDB memory service

Its purpose is to:
- search only scenario-specific saved user messages
- build compact prompt blocks for clarification questions
- expose what was found and what was injected for observability/tests
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from services import history_day_memory_service as memory_svc

logger = logging.getLogger("blabber")

HISTORY_DAY_FACT_SCENARIO_TAG = "history_day_fact"
HISTORY_DAY_IMAGE_SCENARIO_TAG = "history_day_image"
SUPPORTED_MEMORY_SCENARIO_TAGS = (
    HISTORY_DAY_FACT_SCENARIO_TAG,
    HISTORY_DAY_IMAGE_SCENARIO_TAG,
)

DEFAULT_CONTEXT_TOP_K = 3
MAX_CONTEXT_TOP_K = 5
MAX_CONTEXT_ITEMS = 3
MAX_ITEM_TEXT_CHARS = 220
MAX_CONTEXT_BLOCK_CHARS = 1200

MEMORY_DEMO_QUESTIONS = [
    "О чем ты мне только что рассказывал?",
    "С каким годом это связано?",
    "Напомни ключевую фигуру или событие",
]


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def _clip(text: str, limit: int) -> str:
    text = _normalize_text(text)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _iter_unique_by_source(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        source_id = str(item.get("source_id") or "")
        if source_id and source_id in seen:
            continue
        if source_id:
            seen.add(source_id)
        unique.append(item)
    return unique


def _sorted_context_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            -float(item.get("score") or 0.0),
            str(item.get("created_at") or ""),
        ),
    )


def format_saved_context_block(items: list[dict[str, Any]]) -> str:
    """Build a compact injected prompt block from retrieved memory items."""
    if not items:
        return ""

    lines = [
        "[Saved Context From LanceDB]",
        "Используй только этот найденный контекст, если он действительно помогает ответить на уточняющий вопрос.",
        "Если контекст пуст или недостаточен, честно скажи об этом и не выдумывай детали.",
        "Не смешивай этот контекст с unrelated KB или посторонними знаниями.",
    ]

    for idx, item in enumerate(items[:MAX_CONTEXT_ITEMS], start=1):
        score = float(item.get("score") or 0.0)
        scenario_tag = str(item.get("scenario_tag") or "")
        event_date = str(item.get("event_date") or "")
        created_at = str(item.get("created_at") or "")
        text = _clip(str(item.get("text") or ""), MAX_ITEM_TEXT_CHARS)

        meta_bits = [f"score={score:.3f}"]
        if scenario_tag:
            meta_bits.append(f"scenario={scenario_tag}")
        if event_date:
            meta_bits.append(f"date={event_date}")
        if created_at:
            meta_bits.append(f"created_at={created_at}")
        lines.append(f"{idx}. {'; '.join(meta_bits)}")
        lines.append(f"   {text}")

    block = "\n".join(lines).strip()
    return _clip(block, MAX_CONTEXT_BLOCK_CHARS)


def retrieve_saved_context(
    telegram_id: int,
    *,
    query: str,
    top_k: int = DEFAULT_CONTEXT_TOP_K,
    scenario_tags: Iterable[str] | None = None,
) -> dict[str, Any]:
    """
    Retrieve relevant saved context from scenario memory only.

    This layer intentionally does not use `context_service` or KB retrieval.
    """
    query = _normalize_text(query)
    if not query:
        return {
            "ok": True,
            "query": "",
            "items": [],
            "context_block": "",
            "found_count": 0,
            "fallback_used": True,
            "fallback_reason": "empty_query",
        }

    if not memory_svc.is_memory_search_available():
        return {
            "ok": True,
            "query": query,
            "items": [],
            "context_block": "",
            "found_count": 0,
            "fallback_used": True,
            "fallback_reason": "embeddings_unavailable",
        }

    resolved_tags = [tag for tag in (scenario_tags or SUPPORTED_MEMORY_SCENARIO_TAGS) if tag]
    capped_top_k = max(1, min(int(top_k), MAX_CONTEXT_TOP_K))

    recent_saved_messages: list[dict[str, Any]] = []
    for scenario_tag in resolved_tags:
        recent_saved_messages.extend(
            memory_svc.list_saved_messages(
                telegram_id,
                scenario_tag=scenario_tag,
                limit=1,
            )
        )

    raw_items: list[dict[str, Any]] = []
    for scenario_tag in resolved_tags:
        raw_items.extend(
            memory_svc.search_relevant_messages(
                telegram_id,
                query=query,
                scenario_tag=scenario_tag,
                top_k=capped_top_k,
            )
        )

    unique_items = _iter_unique_by_source(_sorted_context_items(raw_items))
    final_items = unique_items[:MAX_CONTEXT_ITEMS]
    context_block = format_saved_context_block(final_items)

    logger.info(
        "history_day_saved_context_retrieved",
        extra={
            "event": "history_day_saved_context_retrieved",
            "telegram_id": telegram_id,
            "query": _clip(query, 180),
            "scenario_tags": resolved_tags,
            "found": len(final_items),
            "injected": bool(context_block),
        },
    )

    return {
        "ok": True,
        "query": query,
        "items": final_items,
        "context_block": context_block,
        "found_count": len(final_items),
        "fallback_used": len(final_items) == 0,
        "fallback_reason": (
            None
            if final_items
            else ("no_saved_messages" if not recent_saved_messages else "no_matches")
        ),
    }
