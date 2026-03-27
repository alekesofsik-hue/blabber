"""
History-day memory service — semantic storage and retrieval for scenario user messages.

Responsibilities:
- accept only user-authored text messages
- compute embeddings via the shared embedding service
- write/read semantic message memory in LanceDB
- degrade safely when embeddings or LanceDB are unavailable
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import repositories.history_day_memory_repo as memory_repo
from repositories.user_repo import get_by_telegram_id
from services import embedding_service as emb_svc

logger = logging.getLogger("blabber")

MAX_TEXT_LEN = 1000
MAX_MESSAGES_PER_USER = 200
DEFAULT_TOP_K = 5
MAX_TOP_K = 10


def _uid(telegram_id: int) -> int | None:
    user = get_by_telegram_id(telegram_id)
    return user["id"] if user else None


def _result(
    *,
    ok: bool,
    action: str,
    message: str,
    source_id: str | None = None,
    fallback_used: bool = False,
    fallback_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "action": action,
        "message": message,
        "source_id": source_id,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
    }


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def _log_event(event: str, **extra: Any) -> None:
    logger.info(event, extra={"event": event, **extra})


def is_memory_search_available() -> bool:
    """Return whether embeddings-backed semantic memory is currently available."""
    return bool(emb_svc.is_available())


def _prune_if_needed(user_db_id: int) -> None:
    """Best-effort pruning for oversized per-user scenario memory."""
    try:
        rows = memory_repo.list_for_user(user_db_id=user_db_id)
        overflow = max(0, len(rows) - MAX_MESSAGES_PER_USER)
        if overflow <= 0:
            return
        stale_source_ids = [str(row["source_id"]) for row in rows[:overflow]]
        memory_repo.delete_by_source_ids(user_db_id=user_db_id, source_ids=stale_source_ids)
        _log_event(
            "history_day_memory_pruned",
            user_db_id=user_db_id,
            deleted=len(stale_source_ids),
            max_messages=MAX_MESSAGES_PER_USER,
        )
    except Exception as exc:
        logger.warning(
            "history_day_memory_prune_failed",
            extra={"event": "history_day_memory_prune_failed", "user_db_id": user_db_id, "error": str(exc)[:200]},
        )


def save_user_message(
    telegram_id: int,
    *,
    role: str,
    text: str,
    scenario_tag: str,
    source_id: str | None = None,
    command_name: str = "",
    source_kind: str = "user_message",
    event_date: str = "",
) -> dict[str, Any]:
    """
    Save one user-authored scenario message into semantic LanceDB memory.
    """
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return _result(ok=False, action="error", message="Пользователь не найден")

    role = (role or "").strip().lower()
    if role != "user":
        return _result(ok=True, action="skipped", message="Сохраняем только пользовательские сообщения")

    text = _normalize_text(text)
    if not text:
        return _result(ok=True, action="skipped", message="Пустое сообщение не сохраняем")
    if text.startswith("/"):
        return _result(ok=True, action="skipped", message="Команды не сохраняем в память сценария")
    if len(text) > MAX_TEXT_LEN:
        text = text[:MAX_TEXT_LEN].rstrip()

    if not emb_svc.is_available():
        _log_event(
            "history_day_memory_save_skipped",
            telegram_id=telegram_id,
            reason="embeddings_unavailable",
            scenario_tag=scenario_tag,
        )
        return _result(
            ok=True,
            action="skipped",
            message="Embeddings недоступны, память сценария не записана",
            fallback_used=True,
            fallback_reason="embeddings_unavailable",
        )

    vector = emb_svc.embed_single(text)
    if not vector:
        _log_event(
            "history_day_memory_save_skipped",
            telegram_id=telegram_id,
            reason="query_embedding_missing",
            scenario_tag=scenario_tag,
        )
        return _result(
            ok=True,
            action="skipped",
            message="Не удалось получить embedding для сообщения",
            fallback_used=True,
            fallback_reason="query_embedding_missing",
        )

    source_id = source_id or uuid.uuid4().hex
    try:
        written = memory_repo.upsert_message(
            user_db_id=user_db_id,
            source_id=source_id,
            text=text,
            vector=vector,
            scenario_tag=scenario_tag,
            created_at=_now_str(),
            command_name=command_name,
            source_kind=source_kind,
            event_date=event_date,
        )
        _prune_if_needed(user_db_id)
    except Exception as exc:
        logger.warning(
            "history_day_memory_write_failed",
            extra={
                "event": "history_day_memory_write_failed",
                "telegram_id": telegram_id,
                "scenario_tag": scenario_tag,
                "error": str(exc)[:200],
            },
        )
        return _result(
            ok=True,
            action="skipped",
            message="Хранилище памяти сценария временно недоступно",
            source_id=source_id,
            fallback_used=True,
            fallback_reason="lancedb_unavailable",
        )

    _log_event(
        "history_day_memory_saved",
        telegram_id=telegram_id,
        scenario_tag=scenario_tag,
        source_id=source_id,
        written=bool(written),
    )
    return _result(
        ok=True,
        action="saved",
        message="Сообщение сохранено в память сценария",
        source_id=source_id,
    )


def search_relevant_messages(
    telegram_id: int,
    *,
    query: str,
    scenario_tag: str | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """
    Search semantic scenario memory for one user.
    """
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return []

    query = _normalize_text(query)
    if not query:
        return []

    if not emb_svc.is_available():
        _log_event(
            "history_day_memory_search_skipped",
            telegram_id=telegram_id,
            reason="embeddings_unavailable",
            scenario_tag=scenario_tag,
        )
        return []

    query_vector = emb_svc.embed_single(query)
    if not query_vector:
        _log_event(
            "history_day_memory_search_skipped",
            telegram_id=telegram_id,
            reason="query_embedding_missing",
            scenario_tag=scenario_tag,
        )
        return []

    try:
        rows = memory_repo.search_by_vector(
            user_db_id=user_db_id,
            query_vector=query_vector,
            top_k=max(1, min(int(top_k), MAX_TOP_K)),
            scenario_tag=scenario_tag,
        )
    except Exception as exc:
        logger.warning(
            "history_day_memory_search_failed",
            extra={
                "event": "history_day_memory_search_failed",
                "telegram_id": telegram_id,
                "scenario_tag": scenario_tag,
                "error": str(exc)[:200],
            },
        )
        return []

    results = [
        {
            **row,
            "score": round(1.0 / (1.0 + max(0.0, float(row.get("distance") or 0.0))), 4),
        }
        for row in rows
    ]
    _log_event(
        "history_day_memory_search_done",
        telegram_id=telegram_id,
        scenario_tag=scenario_tag,
        top_k=min(int(top_k), MAX_TOP_K),
        found=len(results),
    )
    return results


def list_saved_messages(
    telegram_id: int,
    *,
    scenario_tag: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return recent saved scenario messages for one user, newest first."""
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return []
    try:
        rows = memory_repo.list_for_user(user_db_id=user_db_id, scenario_tag=scenario_tag)
    except Exception as exc:
        logger.warning(
            "history_day_memory_list_failed",
            extra={
                "event": "history_day_memory_list_failed",
                "telegram_id": telegram_id,
                "scenario_tag": scenario_tag,
                "error": str(exc)[:200],
            },
        )
        return []

    rows_sorted = sorted(rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return rows_sorted[: max(1, int(limit))]


def clear_user_memory(telegram_id: int, *, scenario_tag: str | None = None) -> bool:
    """Delete all stored scenario memory for a user, optionally scoped by tag."""
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return False
    try:
        memory_repo.delete_all_for_user(user_db_id=user_db_id, scenario_tag=scenario_tag)
        _log_event(
            "history_day_memory_cleared",
            telegram_id=telegram_id,
            scenario_tag=scenario_tag,
        )
        return True
    except Exception as exc:
        logger.warning(
            "history_day_memory_clear_failed",
            extra={
                "event": "history_day_memory_clear_failed",
                "telegram_id": telegram_id,
                "scenario_tag": scenario_tag,
                "error": str(exc)[:200],
            },
        )
        return False
