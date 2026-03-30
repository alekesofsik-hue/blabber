"""
KB rollout helpers for guarded feature delivery.

This module centralizes:
- feature flag resolution (DB config -> env -> default)
- parser mode selection for document ingestion
- compact observability helpers for KB rollout events

Sprint 0 goal: add safe switches and logging without changing the default
behaviour of the existing knowledge base flow.
"""

from __future__ import annotations

import logging
from typing import Any

from services.config_registry import get_setting

logger = logging.getLogger("blabber")

_ROLLOUT_STAGES = {"legacy", "local", "test", "canary", "global"}
_RESERVED_LOG_KEYS = set(logging.makeLogRecord({}).__dict__.keys()) | {"message", "asctime"}


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def is_docling_enabled() -> bool:
    return _as_bool(
        get_setting("kb_docling_enabled", False, env_key="KB_DOCLING_ENABLED"),
        False,
    )


def is_docling_fallback_enabled() -> bool:
    return _as_bool(
        get_setting(
            "kb_docling_fallback_enabled",
            True,
            env_key="KB_DOCLING_FALLBACK_ENABLED",
        ),
        True,
    )


def is_docling_structured_chunks_enabled() -> bool:
    return _as_bool(
        get_setting(
            "kb_docling_structured_chunks_enabled",
            False,
            env_key="KB_DOCLING_STRUCTURED_CHUNKS_ENABLED",
        ),
        False,
    )


def get_rollout_stage() -> str:
    raw = str(
        get_setting(
            "kb_docling_rollout_stage",
            "legacy",
            env_key="KB_DOCLING_ROLLOUT_STAGE",
        )
        or "legacy"
    ).strip().lower()
    if raw in _ROLLOUT_STAGES:
        return raw
    return "legacy"


def get_canary_telegram_ids() -> list[int]:
    raw = get_setting(
        "kb_docling_canary_telegram_ids",
        [],
        env_key="KB_DOCLING_CANARY_TELEGRAM_IDS",
    )
    if raw is None:
        return []
    if isinstance(raw, list):
        items = raw
    else:
        text = str(raw).strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            import json

            try:
                items = json.loads(text)
            except Exception:
                return []
        else:
            items = [part.strip() for part in text.split(",")]

    result: list[int] = []
    for item in items:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return result


def is_doc_summary_enabled() -> bool:
    return _as_bool(
        get_setting("kb_doc_summary_enabled", False, env_key="KB_DOC_SUMMARY_ENABLED"),
        False,
    )


def is_doc_summary_save_enabled() -> bool:
    return _as_bool(
        get_setting(
            "kb_doc_summary_save_enabled",
            False,
            env_key="KB_DOC_SUMMARY_SAVE_ENABLED",
        ),
        False,
    )


def is_structured_retrieval_enabled() -> bool:
    return _as_bool(
        get_setting(
            "kb_structured_retrieval_enabled",
            False,
            env_key="KB_STRUCTURED_RETRIEVAL_ENABLED",
        ),
        False,
    )


def get_doc_parser_mode() -> str:
    """
    Return the effective document parser mode for KB file uploads.

    Modes:
    - legacy_only
    - docling_with_legacy_fallback
    - docling_only
    """
    if not is_docling_enabled():
        return "legacy_only"
    if is_docling_fallback_enabled():
        return "docling_with_legacy_fallback"
    return "docling_only"


def is_docling_active_for_user(telegram_id: int | None = None) -> bool:
    """
    Whether the rollout policy allows Docling for the given user.

    This is a policy helper only. Sprint 0 does not switch parsing behaviour yet.
    """
    if not is_docling_enabled():
        return False

    stage = get_rollout_stage()
    if stage == "legacy":
        return False
    if stage in {"local", "test", "global"}:
        return True
    if stage == "canary":
        if telegram_id is None:
            return False
        return int(telegram_id) in set(get_canary_telegram_ids())
    return False


def should_continue_after_docling_failure() -> bool:
    """Sprint 0 soft-failure policy for future Docling parse errors."""
    return is_docling_fallback_enabled()


def should_continue_without_summary() -> bool:
    """Sprint 0 soft-failure policy for future summary-generation errors."""
    return True


def should_send_summary_after_index_success() -> bool:
    """Sprint 0 UX rule for the future Docling upload flow."""
    return True


def get_rollout_snapshot() -> dict[str, Any]:
    """Resolved KB rollout settings for logging and diagnostics."""
    return {
        "rollout_stage": get_rollout_stage(),
        "canary_user_count": len(get_canary_telegram_ids()),
        "doc_parser_mode": get_doc_parser_mode(),
        "docling_enabled": is_docling_enabled(),
        "docling_fallback_enabled": is_docling_fallback_enabled(),
        "docling_structured_chunks_enabled": is_docling_structured_chunks_enabled(),
        "doc_summary_enabled": is_doc_summary_enabled(),
        "doc_summary_save_enabled": is_doc_summary_save_enabled(),
        "structured_retrieval_enabled": is_structured_retrieval_enabled(),
    }


def log_rollout_event(event: str, **extra: Any) -> None:
    """
    Emit a structured KB rollout event with a config snapshot.

    Keeps the payload compact and consistent across indexing/retrieval paths.
    """
    payload = {"event": event, **get_rollout_snapshot()}
    for key, value in extra.items():
        safe_key = f"kb_{key}" if key in _RESERVED_LOG_KEYS else key
        payload[safe_key] = value
    logger.info(event, extra=payload)
