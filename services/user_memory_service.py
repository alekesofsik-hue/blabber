"""
User memory service — semantic dedup for long-term user facts.

Responsibilities:
- compute embeddings for new memory items
- find nearest existing memory items for the same user
- decide inserted / skipped / updated
- keep SQLite profile rows and LanceDB index in sync
- degrade safely to legacy exact-match behaviour on failures
"""

from __future__ import annotations

import logging
from typing import Any

import repositories.profile_repo as profile_repo
import repositories.user_memory_vector_repo as vector_repo
from repositories.user_repo import get_by_telegram_id, list_users
from services import embedding_service as emb_svc
from services.config_registry import get_setting

logger = logging.getLogger("blabber")

DEFAULT_THRESHOLD = 0.75
DEFAULT_TOP_K = 3
DEFAULT_DECISION_MODE = "skip"


def _uid(telegram_id: int) -> int | None:
    user = get_by_telegram_id(telegram_id)
    return user["id"] if user else None


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: Any, default: float) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_semantic_enabled() -> bool:
    return _as_bool(
        get_setting("user_memory_semantic_enabled", True, env_key="USER_MEMORY_SEMANTIC_ENABLED"),
        True,
    )


def _similarity_threshold() -> float:
    return _as_float(
        get_setting(
            "user_memory_similarity_threshold",
            DEFAULT_THRESHOLD,
            env_key="USER_MEMORY_SIMILARITY_THRESHOLD",
        ),
        DEFAULT_THRESHOLD,
    )


def _decision_mode() -> str:
    raw = str(
        get_setting(
            "user_memory_decision_mode",
            DEFAULT_DECISION_MODE,
            env_key="USER_MEMORY_DECISION_MODE",
        ) or DEFAULT_DECISION_MODE
    ).strip().lower()
    if raw in {"skip", "update"}:
        return raw
    return DEFAULT_DECISION_MODE


def _top_k() -> int:
    return max(
        1,
        _as_int(get_setting("user_memory_top_k", DEFAULT_TOP_K, env_key="USER_MEMORY_TOP_K"), DEFAULT_TOP_K),
    )


def _fallback_result(*, message: str, reason: str, action: str, profile_id: int | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "action": action,
        "profile_id": profile_id,
        "matched_profile_id": None,
        "similarity_score": None,
        "decision_mode": "legacy_exact",
        "fallback_used": True,
        "fallback_reason": reason,
        "message": message,
    }


def _result(
    *,
    ok: bool,
    action: str,
    message: str,
    profile_id: int | None = None,
    matched_profile_id: int | None = None,
    similarity_score: float | None = None,
    decision_mode: str | None = None,
    fallback_used: bool = False,
    fallback_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "action": action,
        "profile_id": profile_id,
        "matched_profile_id": matched_profile_id,
        "similarity_score": similarity_score,
        "decision_mode": decision_mode or _decision_mode(),
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "message": message,
    }


def _runtime_config() -> dict[str, Any]:
    """Return resolved runtime settings for semantic user memory."""
    return {
        "semantic_enabled": _is_semantic_enabled(),
        "similarity_threshold": _similarity_threshold(),
        "decision_mode": _decision_mode(),
        "top_k": _top_k(),
        "embeddings_available": emb_svc.is_available(),
    }


def get_runtime_config() -> dict[str, Any]:
    """Public wrapper for semantic-memory runtime config."""
    return _runtime_config()


def _log_specific_event(telegram_id: int, kind: str, result: dict[str, Any]) -> None:
    fallback_used = bool(result.get("fallback_used"))
    action = str(result.get("action") or "")

    if fallback_used:
        logger.info(
            "user_memory_fallback_exact",
            extra={
                "event": "user_memory_fallback_exact",
                "telegram_id": telegram_id,
                "kind": kind,
                "action": action,
                "profile_id": result.get("profile_id"),
                "matched_profile_id": result.get("matched_profile_id"),
                "similarity_score": result.get("similarity_score"),
                "decision_mode": result.get("decision_mode"),
                "fallback_reason": result.get("fallback_reason"),
            },
        )
        return

    if action == "inserted":
        event = "user_memory_inserted"
    elif action == "updated":
        event = "user_memory_updated"
    elif action == "skipped":
        event = "user_memory_skipped"
    else:
        return

    logger.info(
        event,
        extra={
            "event": event,
            "telegram_id": telegram_id,
            "kind": kind,
            "action": action,
            "profile_id": result.get("profile_id"),
            "matched_profile_id": result.get("matched_profile_id"),
            "similarity_score": result.get("similarity_score"),
            "decision_mode": result.get("decision_mode"),
        },
    )


def _log_save_decision(telegram_id: int, kind: str, result: dict[str, Any]) -> None:
    logger.info(
        "user_memory_save_decision",
        extra={
            "event": "user_memory_save_decision",
            "telegram_id": telegram_id,
            "kind": kind,
            "action": result.get("action"),
            "profile_id": result.get("profile_id"),
            "matched_profile_id": result.get("matched_profile_id"),
            "similarity_score": result.get("similarity_score"),
            "decision_mode": result.get("decision_mode"),
            "fallback_used": result.get("fallback_used"),
            "fallback_reason": result.get("fallback_reason"),
        },
    )
    _log_specific_event(telegram_id, kind, result)


def _log_vector_failure(
    *,
    operation: str,
    telegram_id: int | None = None,
    profile_id: int | None = None,
    error: str,
) -> None:
    logger.warning(
        "user_memory_vector_failed",
        extra={
            "event": "user_memory_vector_failed",
            "operation": operation,
            "telegram_id": telegram_id,
            "profile_id": profile_id,
            "error": error[:200],
        },
    )


def _legacy_add_item(
    telegram_id: int,
    *,
    user_db_id: int,
    kind: str,
    text: str,
    log_result: bool = True,
) -> dict[str, Any]:
    profile_id = profile_repo.add_item_returning_id(user_db_id, fact=text, kind=kind)
    if profile_id is None:
        result = _fallback_result(
            message="Такой факт уже сохранён",
            reason="exact_duplicate_or_semantic_disabled",
            action="skipped",
        )
    else:
        result = _fallback_result(
            message="Запомнил!" if kind != "preference" else "Принято! Буду учитывать.",
            reason="legacy_exact_insert",
            action="inserted",
            profile_id=profile_id,
        )
    if log_result:
        _log_save_decision(telegram_id, kind, result)
    return result


def _is_new_text_better(new_text: str, old_text: str) -> bool:
    """
    Simple deterministic heuristic for update mode.

    Prefer a longer normalized phrasing when it adds meaningfully more detail.
    """
    new_norm = " ".join((new_text or "").split())
    old_norm = " ".join((old_text or "").split())
    if not new_norm or new_norm == old_norm:
        return False
    if len(new_norm) >= len(old_norm) + 8:
        return True
    return False


def _search_similar_by_vector(
    *,
    user_db_id: int,
    kind: str,
    query_vec: list[float],
    top_k: int,
) -> list[dict[str, Any]]:
    raw_results = vector_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=query_vec,
        top_k=max(1, top_k),
    )
    matches: list[dict[str, Any]] = []
    for row in raw_results:
        if (row.get("kind") or "fact") != kind:
            continue
        cand_vec = row.get("vector") or []
        if not cand_vec:
            continue
        similarity = emb_svc.cosine_similarity(query_vec, cand_vec)
        matches.append(
            {
                "profile_id": row["profile_id"],
                "kind": row["kind"],
                "text": row["text"],
                "distance": row.get("distance", 0.0),
                "similarity_score": similarity,
            }
        )
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    return matches[:max(1, top_k)]


def search_similar_memory(
    telegram_id: int,
    *,
    kind: str,
    text: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """
    Return top semantic matches for a text within one user's saved memory.
    """
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return []
    if not _is_semantic_enabled():
        return []
    if not emb_svc.is_available():
        return []

    query_vec = emb_svc.embed_single(text)
    if not query_vec:
        return []

    return _search_similar_by_vector(
        user_db_id=user_db_id,
        kind=kind,
        query_vec=query_vec,
        top_k=max(1, top_k),
    )


def save_memory_item(telegram_id: int, *, kind: str, text: str) -> dict[str, Any]:
    """
    Save a user memory item with semantic dedup when enabled.
    """
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return _result(
            ok=False,
            action="error",
            message="Пользователь не найден",
            decision_mode=_decision_mode(),
        )

    text = (text or "").strip()
    kind = (kind or "fact").strip().lower()
    if not text:
        return _result(ok=False, action="error", message="Текст не может быть пустым")

    if kind != "fact":
        return _legacy_add_item(telegram_id, user_db_id=user_db_id, kind=kind, text=text)

    if not _is_semantic_enabled():
        return _legacy_add_item(telegram_id, user_db_id=user_db_id, kind=kind, text=text)

    if not emb_svc.is_available():
        result = _legacy_add_item(telegram_id, user_db_id=user_db_id, kind=kind, text=text, log_result=False)
        result["fallback_reason"] = "embeddings_unavailable"
        _log_save_decision(telegram_id, kind, result)
        return result

    query_vec = emb_svc.embed_single(text)
    if not query_vec:
        result = _legacy_add_item(telegram_id, user_db_id=user_db_id, kind=kind, text=text, log_result=False)
        result["fallback_reason"] = "query_embedding_missing"
        _log_save_decision(telegram_id, kind, result)
        return result

    try:
        matches = _search_similar_by_vector(
            user_db_id=user_db_id,
            kind=kind,
            query_vec=query_vec,
            top_k=_top_k(),
        )
    except Exception as exc:
        _log_vector_failure(operation="search", telegram_id=telegram_id, error=str(exc))
        result = _legacy_add_item(telegram_id, user_db_id=user_db_id, kind=kind, text=text, log_result=False)
        result["fallback_reason"] = "vector_search_failed"
        _log_save_decision(telegram_id, kind, result)
        return result

    threshold = _similarity_threshold()
    mode = _decision_mode()
    best = matches[0] if matches else None

    if not best or float(best["similarity_score"]) < threshold:
        profile_id = profile_repo.add_item_returning_id(user_db_id, fact=text, kind=kind)
        if profile_id is None:
            result = _result(
                ok=True,
                action="skipped",
                message="Такой факт уже сохранён",
                decision_mode=mode,
            )
            _log_save_decision(telegram_id, kind, result)
            return result

        try:
            vector_repo.upsert_item(
                user_db_id=user_db_id,
                profile_id=profile_id,
                kind=kind,
                text=text,
                vector=query_vec,
            )
            result = _result(
                ok=True,
                action="inserted",
                profile_id=profile_id,
                message="Запомнил!",
                decision_mode=mode,
            )
        except Exception as exc:
            _log_vector_failure(
                operation="write_insert",
                telegram_id=telegram_id,
                profile_id=profile_id,
                error=str(exc),
            )
            result = _result(
                ok=True,
                action="inserted",
                profile_id=profile_id,
                message="Запомнил!",
                decision_mode=mode,
                fallback_used=True,
                fallback_reason="vector_write_failed",
            )
        _log_save_decision(telegram_id, kind, result)
        return result

    matched_profile_id = int(best["profile_id"])
    similarity_score = round(float(best["similarity_score"]), 4)

    if mode == "update":
        existing = profile_repo.get_item_by_id(matched_profile_id, user_db_id)
        if existing and _is_new_text_better(text, existing.get("fact", "")):
            updated = profile_repo.update_item_text(matched_profile_id, user_db_id, fact=text)
            if updated:
                try:
                    vector_repo.upsert_item(
                        user_db_id=user_db_id,
                        profile_id=matched_profile_id,
                        kind=kind,
                        text=text,
                        vector=query_vec,
                    )
                    result = _result(
                        ok=True,
                        action="updated",
                        profile_id=matched_profile_id,
                        matched_profile_id=matched_profile_id,
                        similarity_score=similarity_score,
                        decision_mode=mode,
                        message="Нашёл похожий факт и обновил его более удачной формулировкой.",
                    )
                except Exception as exc:
                    _log_vector_failure(
                        operation="write_update",
                        telegram_id=telegram_id,
                        profile_id=matched_profile_id,
                        error=str(exc),
                    )
                    result = _result(
                        ok=True,
                        action="updated",
                        profile_id=matched_profile_id,
                        matched_profile_id=matched_profile_id,
                        similarity_score=similarity_score,
                        decision_mode=mode,
                        fallback_used=True,
                        fallback_reason="vector_write_failed",
                        message="Нашёл похожий факт и обновил его более удачной формулировкой.",
                    )
                _log_save_decision(telegram_id, kind, result)
                return result

    result = _result(
        ok=True,
        action="skipped",
        matched_profile_id=matched_profile_id,
        similarity_score=similarity_score,
        decision_mode=mode,
        message="Похожий факт уже есть, не стал дублировать.",
    )
    _log_save_decision(telegram_id, kind, result)
    return result


def reindex_user_memory(telegram_id: int) -> dict[str, Any]:
    """
    Rebuild one user's semantic memory index from SQLite profile rows.
    """
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return {"ok": False, "indexed": 0, "message": "Пользователь не найден"}
    if not emb_svc.is_available():
        return {"ok": False, "indexed": 0, "message": "Для переиндексации нужен OPENAI_API_KEY"}

    items = profile_repo.get_items_with_ids(user_db_id)
    facts = [item for item in items if (item.get("kind") or "fact") == "fact"]
    if not facts:
        vector_repo.delete_all_for_user(user_db_id=user_db_id)
        return {"ok": True, "indexed": 0, "message": "Индекс очищен: фактов для индексации нет"}

    texts = [item["fact"] for item in facts]
    vectors = emb_svc.embed_texts(texts)
    if not vectors or len(vectors) != len(facts):
        return {"ok": False, "indexed": 0, "message": "Не удалось пересчитать embeddings"}

    rows = [
        {
            "profile_id": item["id"],
            "kind": item.get("kind") or "fact",
            "text": item["fact"],
            "vector": vector,
        }
        for item, vector in zip(facts, vectors)
    ]
    written = vector_repo.replace_all_for_user(user_db_id=user_db_id, items=rows)
    return {"ok": True, "indexed": written, "message": f"Переиндексация завершена: {written}"}


def reindex_many_users(
    *,
    telegram_ids: list[int] | None = None,
    page_size: int = 100,
    limit_users: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Reindex semantic memory for multiple users.

    If `telegram_ids` is omitted, iterates through all known users page by page.
    """
    selected_ids: list[int]
    if telegram_ids is not None:
        selected_ids = list(dict.fromkeys(int(tid) for tid in telegram_ids))
    else:
        selected_ids = []
        offset = 0
        while True:
            batch = list_users(offset=offset, limit=page_size)
            if not batch:
                break
            selected_ids.extend(int(row["telegram_id"]) for row in batch if row.get("telegram_id") is not None)
            if len(batch) < page_size:
                break
            offset += page_size

    if limit_users is not None and limit_users >= 0:
        selected_ids = selected_ids[:limit_users]

    summary = {
        "ok": True,
        "dry_run": dry_run,
        "requested": len(selected_ids),
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "total_indexed": 0,
        "results": [],
    }

    if dry_run:
        summary["processed"] = len(selected_ids)
        summary["succeeded"] = len(selected_ids)
        summary["results"] = [{"telegram_id": tid, "ok": True, "indexed": None, "message": "dry-run"} for tid in selected_ids]
        return summary

    for tid in selected_ids:
        try:
            result = reindex_user_memory(tid)
        except Exception as exc:
            logger.warning(
                "user_memory_reindex_failed",
                extra={"error": str(exc)[:200], "telegram_id": tid},
            )
            result = {"ok": False, "indexed": 0, "message": str(exc)}

        indexed = int(result.get("indexed") or 0)
        ok = bool(result.get("ok"))
        summary["processed"] += 1
        summary["total_indexed"] += indexed
        if ok:
            summary["succeeded"] += 1
        else:
            summary["failed"] += 1
        summary["results"].append(
            {
                "telegram_id": tid,
                "ok": ok,
                "indexed": indexed,
                "message": result.get("message"),
            }
        )

    return summary


def diagnose_user_memory(
    telegram_id: int,
    *,
    text: str,
    kind: str = "fact",
    top_k: int | None = None,
) -> dict[str, Any]:
    """
    Return a safe diagnostics snapshot for one input text without writing data.
    """
    user_db_id = _uid(telegram_id)
    config = _runtime_config()
    if user_db_id is None:
        return {
            "ok": False,
            "message": "Пользователь не найден",
            "config": config,
            "matches": [],
        }

    items = profile_repo.get_items_with_ids(user_db_id)
    fact_count = sum(1 for item in items if (item.get("kind") or "fact") == "fact")
    pref_count = sum(1 for item in items if (item.get("kind") or "fact") == "preference")

    matches = search_similar_memory(
        telegram_id,
        kind=kind,
        text=text,
        top_k=top_k or config["top_k"],
    )
    sanitized_matches = [
        {
            "profile_id": row.get("profile_id"),
            "kind": row.get("kind"),
            "similarity_score": round(float(row.get("similarity_score") or 0.0), 4),
            "distance": round(float(row.get("distance") or 0.0), 4),
            "text_preview": str(row.get("text") or "")[:80],
        }
        for row in matches
    ]
    return {
        "ok": True,
        "message": "ok",
        "config": config,
        "user": {
            "telegram_id": telegram_id,
            "user_db_id": user_db_id,
            "fact_count": fact_count,
            "preference_count": pref_count,
        },
        "matches": sanitized_matches,
    }


def delete_memory_item(telegram_id: int, profile_id: int) -> bool:
    """
    Delete one semantic memory index row after profile deletion.

    Returns True on best effort. Storage errors are soft failures for callers.
    """
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return False
    try:
        vector_repo.delete_by_profile_id(user_db_id=user_db_id, profile_id=profile_id)
        return True
    except Exception as exc:
        _log_vector_failure(
            operation="delete_one",
            telegram_id=telegram_id,
            profile_id=profile_id,
            error=str(exc),
        )
        return False


def clear_user_memory_index(telegram_id: int) -> bool:
    """Delete a user's full semantic memory index."""
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return False
    try:
        vector_repo.delete_all_for_user(user_db_id=user_db_id)
        return True
    except Exception as exc:
        _log_vector_failure(operation="delete_all", telegram_id=telegram_id, error=str(exc))
        return False

