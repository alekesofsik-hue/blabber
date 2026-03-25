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
import services.user_memory_service as user_memory_svc

logger = logging.getLogger("blabber")

MAX_FACTS: int = 20
MAX_FACT_LEN: int = 300
ALLOWED_KINDS: set[str] = {"fact", "preference"}


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


def get_items_with_ids(telegram_id: int) -> list[dict]:
    uid = _uid(telegram_id)
    if uid is None:
        return []
    try:
        return profile_repo.get_items_with_ids(uid)
    except Exception as exc:
        logger.warning("profile_get_items_with_ids_failed", extra={"error": str(exc)})
        return []


def add_fact(telegram_id: int, fact: str) -> tuple[bool, str]:
    """Add a personal fact. Returns (success, message)."""
    return add_item(telegram_id, kind="fact", text=fact)


def add_preference(telegram_id: int, text: str) -> tuple[bool, str]:
    """Add a user preference (style / constraints). Returns (success, message)."""
    return add_item(telegram_id, kind="preference", text=text)


def add_item(telegram_id: int, *, kind: str, text: str) -> tuple[bool, str]:
    """Add a profile item (fact/preference). Returns (success, message)."""
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"

    kind = (kind or "").strip().lower()
    if kind not in ALLOWED_KINDS:
        return False, "Неизвестный тип памяти"

    fact = (text or "").strip()
    if not fact:
        return False, "Текст не может быть пустым"
    if len(fact) > MAX_FACT_LEN:
        return False, f"Слишком длинно, макс. {MAX_FACT_LEN} символов"

    count = profile_repo.count_facts(uid)
    if count >= MAX_FACTS:
        return False, f"Достигнут лимит ({MAX_FACTS} пунктов). Удали лишнее через /profile"

    try:
        if kind == "fact":
            result = user_memory_svc.save_memory_item(telegram_id, kind=kind, text=fact)
            if not result.get("ok"):
                return False, result.get("message") or "Ошибка при сохранении"
            return True, result.get("message") or "Запомнил!"

        added = profile_repo.add_item(uid, fact=fact, kind=kind)
        if not added:
            return False, "Такой факт уже сохранён"
        if kind == "preference":
            return True, "Принято! Буду учитывать."
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
        item = profile_repo.get_item_by_id(profile_id, uid)
        deleted = profile_repo.delete_fact_by_id(profile_id, uid)
        if not deleted:
            return False, "Факт не найден"
        if item and (item.get("kind") or "fact") == "fact":
            user_memory_svc.delete_memory_item(telegram_id, profile_id)
        return True, "Забыл!"
    except Exception as exc:
        logger.warning("profile_delete_fact_failed", extra={"error": str(exc)})
        return False, "Ошибка при удалении"


def clear_facts(telegram_id: int) -> None:
    uid = _uid(telegram_id)
    if uid is None:
        return
    try:
        items = profile_repo.get_items_with_ids(uid)
        profile_repo.delete_all_facts(uid)
        if any((item.get("kind") or "fact") == "fact" for item in items):
            user_memory_svc.clear_user_memory_index(telegram_id)
    except Exception as exc:
        logger.warning("profile_clear_facts_failed", extra={"error": str(exc)})


def build_profile_context(telegram_id: int) -> str | None:
    """
    Build a context string to inject as an assistant note before the current turn.
    Returns None if the user has no saved facts.
    """
    items = get_items_with_ids(telegram_id)
    if not items:
        return None

    prefs = [i["fact"] for i in items if (i.get("kind") or "fact") == "preference"]
    facts = [i["fact"] for i in items if (i.get("kind") or "fact") != "preference"]

    parts: list[str] = []
    if prefs:
        parts.append("Предпочтения:")
        parts.extend(f"• {p}" for p in prefs)
    if facts:
        if parts:
            parts.append("")
        parts.append("Факты:")
        parts.extend(f"• {f}" for f in facts)

    return "[Что я знаю о собеседнике:\n" + "\n".join(parts) + "\n]"
