"""
Profile service — long-term memory D: personal facts about each user.

Facts are stored in SQLite and survive context resets, model switches and
bot restarts.  They get injected into every LLM call as an "assistant note"
so the bot naturally remembers user preferences without exposing the list.
"""

from __future__ import annotations

import logging

import repositories.profile_repo as profile_repo
from repositories.user_repo import get_by_telegram_id

logger = logging.getLogger("blabber")

MAX_FACTS: int = 20
MAX_FACT_LEN: int = 300


def _uid(telegram_id: int) -> int | None:
    user = get_by_telegram_id(telegram_id)
    return user["id"] if user else None


def get_facts(telegram_id: int) -> list[str]:
    uid = _uid(telegram_id)
    if uid is None:
        return []
    try:
        return profile_repo.get_facts(uid)
    except Exception as exc:
        logger.warning("profile_get_facts_failed", extra={"error": str(exc)})
        return []


def get_facts_with_ids(telegram_id: int) -> list[dict]:
    uid = _uid(telegram_id)
    if uid is None:
        return []
    try:
        return profile_repo.get_facts_with_ids(uid)
    except Exception as exc:
        logger.warning("profile_get_facts_with_ids_failed", extra={"error": str(exc)})
        return []


def add_fact(telegram_id: int, fact: str) -> tuple[bool, str]:
    """Add a personal fact. Returns (success, message)."""
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"

    fact = fact.strip()
    if not fact:
        return False, "Факт не может быть пустым"
    if len(fact) > MAX_FACT_LEN:
        return False, f"Слишком длинно, макс. {MAX_FACT_LEN} символов"

    count = profile_repo.count_facts(uid)
    if count >= MAX_FACTS:
        return False, f"Достигнут лимит ({MAX_FACTS} фактов). Удали лишнее через /profile"

    try:
        added = profile_repo.add_fact(uid, fact)
        if not added:
            return False, "Такой факт уже сохранён"
        return True, "Запомнил!"
    except Exception as exc:
        logger.warning("profile_add_fact_failed", extra={"error": str(exc)})
        return False, "Ошибка при сохранении"


def delete_fact_by_id(telegram_id: int, profile_id: int) -> tuple[bool, str]:
    """Delete a fact by its profile row id."""
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"
    try:
        deleted = profile_repo.delete_fact_by_id(profile_id, uid)
        if not deleted:
            return False, "Факт не найден"
        return True, "Забыл!"
    except Exception as exc:
        logger.warning("profile_delete_fact_failed", extra={"error": str(exc)})
        return False, "Ошибка при удалении"


def clear_facts(telegram_id: int) -> None:
    uid = _uid(telegram_id)
    if uid is None:
        return
    try:
        profile_repo.delete_all_facts(uid)
    except Exception as exc:
        logger.warning("profile_clear_facts_failed", extra={"error": str(exc)})


def build_profile_context(telegram_id: int) -> str | None:
    """
    Build a context string to inject as an assistant note before the current turn.
    Returns None if the user has no saved facts.
    """
    facts = get_facts(telegram_id)
    if not facts:
        return None
    lines = "\n".join(f"• {f}" for f in facts)
    return f"[Что я знаю о собеседнике:\n{lines}\n]"
