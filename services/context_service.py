"""
Context service — manages multi-turn conversation history for the bot.

Design decisions:
- One shared context per user regardless of which LLM model is active.
- Rolling window of CONTEXT_WINDOW messages + compressed summary of older turns.
- Auto-clear after CONTEXT_TTL_MINUTES of inactivity.
- Summarisation is text-only (no LLM call): compact concatenation capped at 1 500 chars.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import repositories.context_repo as ctx_repo
from repositories.user_repo import get_by_telegram_id

logger = logging.getLogger("blabber")

# ── Tuning constants ──────────────────────────────────────────────────────────
CONTEXT_WINDOW: int = 10          # max messages kept in the rolling window
CONTEXT_TRIM_AFTER: int = 20      # trigger summarise-and-trim when count exceeds this
CONTEXT_TTL_MINUTES: int = 60     # inactivity window before auto-clear
SUMMARY_MAX_CHARS: int = 1_500    # hard cap on stored summary text


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_user_db_id(telegram_id: int) -> int | None:
    """Look up the internal users.id from telegram_id."""
    user = get_by_telegram_id(telegram_id)
    return user["id"] if user else None


def _is_stale(last_activity_str: str | None) -> bool:
    """Return True if last_activity_str is older than CONTEXT_TTL_MINUTES."""
    if not last_activity_str:
        return False
    try:
        last_dt = datetime.strptime(last_activity_str, "%Y-%m-%d %H:%M:%S")
        # SQLite stores UTC; compare against UTC now
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        age_minutes = (now_utc - last_dt).total_seconds() / 60
        return age_minutes > CONTEXT_TTL_MINUTES
    except Exception:
        return False


def _build_summary(old_messages: list[dict[str, Any]], existing_summary: str) -> str:
    """
    Build a compressed text summary from a list of {role, content} messages.
    Prepends existing_summary so history is not lost when we trim multiple times.
    """
    parts: list[str] = []
    if existing_summary:
        parts.append(existing_summary)

    for m in old_messages:
        label = "User" if m["role"] == "user" else "Bot"
        snippet = (m["content"] or "").replace("\n", " ").strip()
        if len(snippet) > 300:
            snippet = snippet[:300] + "…"
        parts.append(f"{label}: {snippet}")

    full = "\n".join(parts)
    if len(full) > SUMMARY_MAX_CHARS:
        # Keep the tail (most recent is most valuable)
        full = "…" + full[-(SUMMARY_MAX_CHARS - 1):]
    return full


# ── Public API ────────────────────────────────────────────────────────────────

def get_mode(telegram_id: int) -> str:
    """Return 'chat' or 'single'. Falls back to 'single' if user not found."""
    try:
        return ctx_repo.get_context_mode(telegram_id)
    except Exception as exc:
        logger.warning("context_get_mode_failed", extra={"error": str(exc)})
        return "single"


def set_mode(telegram_id: int, mode: str) -> bool:
    """
    Set context mode for user.

    Args:
        telegram_id: Telegram user ID
        mode: 'chat' or 'single'

    Returns:
        True on success, False if user not found or DB error.
    """
    if mode not in ("chat", "single"):
        return False
    try:
        ctx_repo.set_context_mode(telegram_id, mode)
        return True
    except Exception as exc:
        logger.warning("context_set_mode_failed", extra={"error": str(exc)})
        return False


def get_history(telegram_id: int) -> list[dict[str, str]]:
    """
    Return conversation history ready to inject as messages before the current turn.

    Format: list of {"role": "user"|"assistant", "content": "..."}

    Side-effect: if last activity is older than TTL, auto-clears context and returns [].
    """
    uid = _get_user_db_id(telegram_id)
    if uid is None:
        return []

    try:
        # Auto-clear on TTL
        last_activity = ctx_repo.get_last_activity(uid)
        if _is_stale(last_activity):
            _clear_by_db_id(uid)
            logger.info(
                "context_ttl_cleared",
                extra={"event": "context_ttl_cleared", "telegram_id": telegram_id},
            )
            return []

        summary = ctx_repo.get_summary(uid)
        messages = ctx_repo.get_messages(uid)

        history: list[dict[str, str]] = []
        if summary:
            # Inject summary as a system-style note attributed to assistant so
            # it fits the user/assistant alternation expected by all providers.
            history.append(
                {"role": "assistant", "content": f"[Краткое резюме предыдущей беседы: {summary}]"}
            )
        history.extend({"role": m["role"], "content": m["content"]} for m in messages)
        return history

    except Exception as exc:
        logger.warning("context_get_history_failed", extra={"error": str(exc)})
        return []


def add_turn(telegram_id: int, user_msg: str, assistant_msg: str) -> None:
    """
    Persist a user+assistant turn to the rolling window.
    Triggers summarise-and-trim when window exceeds CONTEXT_TRIM_AFTER.
    """
    uid = _get_user_db_id(telegram_id)
    if uid is None:
        return

    try:
        ctx_repo.add_message(uid, "user", user_msg)
        ctx_repo.add_message(uid, "assistant", assistant_msg)
        _maybe_trim(uid)
    except Exception as exc:
        logger.warning("context_add_turn_failed", extra={"error": str(exc)})


def clear_context(telegram_id: int) -> None:
    """Delete all conversation history and summary for user."""
    uid = _get_user_db_id(telegram_id)
    if uid is None:
        return
    _clear_by_db_id(uid)


def _clear_by_db_id(uid: int) -> None:
    """Internal clear by users.id."""
    try:
        ctx_repo.delete_messages(uid)
        ctx_repo.delete_summary(uid)
    except Exception as exc:
        logger.warning("context_clear_failed", extra={"error": str(exc)})


def get_message_count(telegram_id: int) -> int:
    """Return how many messages are currently stored for user."""
    uid = _get_user_db_id(telegram_id)
    if uid is None:
        return 0
    try:
        return ctx_repo.count_messages(uid)
    except Exception:
        return 0


def _maybe_trim(uid: int) -> None:
    """
    If message count exceeds CONTEXT_TRIM_AFTER, summarise oldest
    (count - CONTEXT_WINDOW) messages and delete them.
    """
    count = ctx_repo.count_messages(uid)
    if count <= CONTEXT_TRIM_AFTER:
        return

    n_to_trim = count - CONTEXT_WINDOW
    old_msgs = ctx_repo.pop_oldest_messages(uid, n_to_trim)
    existing_summary = ctx_repo.get_summary(uid)
    new_summary = _build_summary(old_msgs, existing_summary)
    ctx_repo.set_summary(uid, new_summary)

    logger.info(
        "context_trimmed",
        extra={
            "event": "context_trimmed",
            "trimmed": n_to_trim,
            "remaining": CONTEXT_WINDOW,
        },
    )
