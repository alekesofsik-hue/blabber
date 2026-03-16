"""
Auto memory service — suggests useful long-term memory items (facts & preferences)
based on the recent conversation, with explicit user confirmation.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import repositories.auto_memory_repo as am_repo
import repositories.context_repo as ctx_repo
from repositories.user_repo import get_by_telegram_id
from services import profile_service
from utils import get_chat_response

logger = logging.getLogger("blabber")

# Tunables
SUGGEST_EVERY_TURNS: int = 6
COOLDOWN_MINUTES: int = 30
MAX_ITEMS: int = 5
MAX_EVIDENCE_LEN: int = 160


EXTRACT_SYSTEM_PROMPT = """
Ты — модуль извлечения полезной долгосрочной памяти о пользователе из диалога с ассистентом.

Задача: предложить 1–5 пунктов, которые стоит сохранить в профиль пользователя.

Правила:
- Добавляй только то, что пользователь ЯВНО сказал о себе или своих предпочтениях.
- Не добавляй догадки, выводы, интерпретации и то, что сказал ассистент.
- Предпочитай устойчивые вещи: имя, роль/профессия, проект, язык, формат ответов, ограничения ("кратко", "без воды", "без эмодзи" и т.п.).
- Избегай чувствительных данных (пароли, токены, номера карт, адреса и т.п.) — если встретилось, НЕ сохраняй.

Верни ТОЛЬКО валидный JSON-массив объектов (без markdown, без текста вокруг), структура:
[
  {"kind":"preference"|"fact", "text":"<коротко, до 120 символов>", "evidence":"<короткая цитата пользователя>"}
]
""".strip()


def _uid(telegram_id: int) -> int | None:
    user = get_by_telegram_id(telegram_id)
    return user["id"] if user else None


def _is_cooldown_passed(last_suggested_at: str | None) -> bool:
    if not last_suggested_at:
        return True
    try:
        last_dt = datetime.strptime(last_suggested_at, "%Y-%m-%d %H:%M:%S")
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        age_min = (now_utc - last_dt).total_seconds() / 60
        return age_min >= COOLDOWN_MINUTES
    except Exception:
        return True


def _parse_json_array(raw: str) -> list[dict[str, Any]]:
    cleaned = re.sub(r"```(?:json)?\s*", "", (raw or "")).strip().rstrip("`").strip()
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group())
            return data if isinstance(data, list) else []
        except Exception:
            return []


def _safe_text(s: str, *, limit: int) -> str:
    s = (s or "").strip().replace("\n", " ")
    if len(s) > limit:
        return s[:limit].rstrip() + "…"
    return s


def _build_dialog_for_extraction(messages: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for m in messages:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        label = "Пользователь" if role == "user" else "Ассистент"
        lines.append(f"{label}: {content}")
    return "\n\n".join(lines)


def _pick_extraction_model(fallback_model: str) -> str:
    # Prefer OpenAI for structured extraction if available, else use the current model.
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return fallback_model or "openrouter"


def _filter_candidates(
    candidates: list[dict[str, Any]],
    *,
    dialog_text: str,
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    for c in candidates:
        kind = str(c.get("kind") or "").strip().lower()
        text = str(c.get("text") or "").strip()
        evidence = str(c.get("evidence") or "").strip()

        if kind not in ("fact", "preference"):
            continue
        if not text or len(text) > profile_service.MAX_FACT_LEN:
            continue

        # Rough safety: avoid storing anything that looks like a secret/token.
        if re.search(r"\b(sk-[a-z0-9]{10,}|ya29\.[a-z0-9_-]{10,}|api[_-]?key)\b", text, re.I):
            continue

        # Evidence must appear in dialog (helps prevent hallucinated "facts").
        if evidence and evidence not in dialog_text:
            continue

        norm = (kind + ":" + text.lower()).strip()
        if norm in seen:
            continue
        seen.add(norm)

        out.append(
            {
                "kind": kind,
                "text": _safe_text(text, limit=profile_service.MAX_FACT_LEN),
                "evidence": _safe_text(evidence, limit=MAX_EVIDENCE_LEN),
                "status": "pending",
            }
        )

        if len(out) >= MAX_ITEMS:
            break

    return out


def maybe_create_suggestion(
    *,
    telegram_id: int,
    selected_model: str,
) -> tuple[str, list[dict[str, str]]] | None:
    """
    Return (suggestion_id, items) or None if nothing to suggest / not eligible.
    Also persists suggestion payload to DB when created.
    """
    settings = am_repo.get_user_settings(telegram_id)
    if not settings:
        return None

    user_db_id = settings["user_db_id"]
    if not settings["enabled"]:
        return None

    if not _is_cooldown_passed(settings["last_suggested_at"]):
        return None

    # Only in chat mode and only after enough turns accumulated.
    msg_count = ctx_repo.count_messages(user_db_id)
    turns = msg_count // 2
    if turns < SUGGEST_EVERY_TURNS or turns % SUGGEST_EVERY_TURNS != 0:
        return None

    # Do not suggest if profile is full.
    if profile_service.get_facts(telegram_id) and len(profile_service.get_facts(telegram_id)) >= profile_service.MAX_FACTS:
        return None

    # Use last ~12 messages (6 turns) for extraction.
    messages = ctx_repo.get_messages(user_db_id)[-12:]
    dialog_text = _build_dialog_for_extraction(messages)
    if not dialog_text:
        return None

    extraction_model = _pick_extraction_model(selected_model)

    logger.info(
        "auto_memory_extract_started",
        extra={
            "event": "auto_memory_extract_started",
            "telegram_id": telegram_id,
            "model": extraction_model,
            "turns": turns,
        },
    )

    raw, _ = get_chat_response(
        user_message=dialog_text,
        model=extraction_model,
        system_message=EXTRACT_SYSTEM_PROMPT,
        telegram_id=telegram_id,
    )
    candidates = _parse_json_array(raw)
    items = _filter_candidates(candidates, dialog_text=dialog_text)
    if not items:
        return None

    suggestion_id = uuid.uuid4().hex[:10]
    am_repo.create_suggestion(suggestion_id, user_db_id, json.dumps(items, ensure_ascii=False))
    am_repo.touch_last_suggested(user_db_id)

    logger.info(
        "auto_memory_suggestion_created",
        extra={
            "event": "auto_memory_suggestion_created",
            "telegram_id": telegram_id,
            "suggestion_id": suggestion_id,
            "items": len(items),
        },
    )

    return suggestion_id, items


def apply_suggestion_item(
    *,
    telegram_id: int,
    suggestion_id: str,
    item_index: int,
) -> tuple[bool, str, list[dict[str, str]] | None]:
    """Apply a single item from suggestion. Returns (ok, message, updated_items_or_none)."""
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return False, "Пользователь не найден", None

    row = am_repo.get_suggestion(suggestion_id, user_db_id)
    if not row or row.get("status") != "pending":
        return False, "Предложение уже недоступно.", None

    try:
        items = json.loads(row["items_json"])
    except Exception:
        return False, "Не удалось прочитать предложение.", None

    if not isinstance(items, list) or not (0 <= item_index < len(items)):
        return False, "Некорректный пункт.", None

    item = items[item_index] or {}
    if item.get("status") == "saved":
        return True, "Уже сохранено.", items

    kind = str(item.get("kind") or "fact")
    text = str(item.get("text") or "").strip()
    if not text:
        return False, "Пустой пункт.", items

    if kind == "preference":
        ok, msg = profile_service.add_preference(telegram_id, text)
    else:
        ok, msg = profile_service.add_fact(telegram_id, text)

    if ok:
        item["status"] = "saved"
        items[item_index] = item
        am_repo.update_items_json(suggestion_id, user_db_id, json.dumps(items, ensure_ascii=False))
    return ok, msg, items


def dismiss_suggestion(*, telegram_id: int, suggestion_id: str, status: str) -> None:
    user_db_id = _uid(telegram_id)
    if user_db_id is None:
        return
    am_repo.set_status(suggestion_id, user_db_id, status)


def set_enabled(telegram_id: int, enabled: bool) -> bool:
    return am_repo.set_enabled(telegram_id, enabled)


def get_settings(telegram_id: int) -> dict | None:
    return am_repo.get_user_settings(telegram_id)

