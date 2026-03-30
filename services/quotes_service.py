"""
Quotes service — "Смешные фразы Балабола".

Users can save funny/interesting phrases said by the bot and search them
semantically. This module bridges the repository layer with business logic:
deduplication check, embedding generation, fallback to keyword search.
"""

from __future__ import annotations

import logging
from typing import Literal

import services.embedding_service as emb_svc
import repositories.quotes_repo as quotes_repo

logger = logging.getLogger("blabber")

SearchMode = Literal["semantic", "keyword"]

MAX_QUOTE_LEN = 1000
MAX_QUOTES = 500
# Сколько фраз на странице /quotes list (полный текст + клавиатура в одном сообщении, лимит TG 4096)
LIST_PAGE_SIZE = 3


def add_quote(telegram_id: int, text: str) -> tuple[bool, str]:
    """
    Save a quote to the collection.

    Returns (ok, message).
    """
    text = text.strip()
    if not text:
        return False, "Текст не может быть пустым."

    if len(text) > MAX_QUOTE_LEN:
        return False, f"Фраза слишком длинная (максимум {MAX_QUOTE_LEN} символов)."

    count = quotes_repo.get_quote_count(telegram_id)
    if count >= MAX_QUOTES:
        return False, f"Достигнут лимит ({MAX_QUOTES} фраз). Удали лишнее в /quotes list или: /quotes del id."

    # Compute embedding (graceful degradation: None if key missing)
    vector = emb_svc.embed_single(text)

    try:
        quotes_repo.add_quote(telegram_id, text, vector)
    except ValueError as exc:
        return False, f"Ошибка: {exc}"
    except Exception as exc:
        logger.exception("quotes_add_failed", extra={"error": str(exc)[:200]})
        return False, "Не удалось сохранить фразу. Попробуй позже."

    total = count + 1
    if vector is None:
        return True, f"💾 Сохранено! (#{total}) — без семантики (нет OpenAI ключа)"
    return True, f"💾 Сохранено! (#{total})"


def delete_quote(telegram_id: int, quote_id: int) -> tuple[bool, str]:
    """Delete a specific quote by its list number (SQLite id)."""
    ok = quotes_repo.delete_quote(telegram_id, quote_id)
    if ok:
        return True, "🗑 Фраза удалена."
    return False, "Фраза не найдена или принадлежит другому пользователю."


def clear_all(telegram_id: int) -> tuple[bool, str]:
    """Delete all quotes for the user."""
    count = quotes_repo.delete_all_quotes(telegram_id)
    if count == 0:
        return False, "Коллекция уже пуста."
    return True, f"🗑 Коллекция очищена ({count} фраз удалено)."


def get_random(telegram_id: int) -> dict | None:
    """Return a random quote dict or None if collection is empty."""
    return quotes_repo.get_random_quote(telegram_id)


def get_recent(telegram_id: int, limit: int = 10) -> list[dict]:
    """Return last N quotes (newest first)."""
    return quotes_repo.get_recent_quotes(telegram_id, limit=limit)


def list_page(telegram_id: int, page: int) -> tuple[list[dict], int, int, int]:
    """
    Одна страница списка цитат для /quotes list.

    Returns:
        (items, total_count, total_pages, current_page_zero_based)
    """
    total = quotes_repo.get_quote_count(telegram_id)
    if total == 0:
        return [], 0, 0, 0
    total_pages = max(1, (total + LIST_PAGE_SIZE - 1) // LIST_PAGE_SIZE)
    page = max(0, min(int(page), total_pages - 1))
    offset = page * LIST_PAGE_SIZE
    items = quotes_repo.get_quotes_page(telegram_id, offset, LIST_PAGE_SIZE)
    return items, total, total_pages, page


def get_count(telegram_id: int) -> int:
    return quotes_repo.get_quote_count(telegram_id)


def _closeness_from_distance(distance: float) -> tuple[int, str]:
    """
    Условная «оценка близости» 0–99% и короткая метка для новичка.
    d — метрика поиска LanceDB (меньше = ближе); формула — для наглядности, не научная.
    """
    d = max(0.0, float(distance))
    pct = max(0, min(99, int(100.0 / (1.0 + d))))
    if pct >= 72:
        label = "🟢 очень близко"
    elif pct >= 48:
        label = "🟡 близко"
    else:
        label = "🟠 слабее"
    return pct, label


def search(telegram_id: int, query: str, top_k: int = 5) -> tuple[list[dict], SearchMode]:
    """
    Поиск по смыслу (семантика) или по подстроке.

    Каждый элемент:
      semantic: id, text, added_at, distance, closeness_pct, closeness_label
      keyword: id, text, added_at (как в text_search)
    """
    query = query.strip()
    if not query:
        return [], "keyword"

    if emb_svc.is_available():
        vector = emb_svc.embed_single(query)
        if vector:
            raw = quotes_repo.semantic_search(telegram_id, vector, top_k=top_k)
            if raw:
                enriched: list[dict] = []
                for r in raw:
                    lid = r.get("lance_id") or ""
                    dist = float(r.get("distance", 0.0))
                    pct, label = _closeness_from_distance(dist)
                    meta = quotes_repo.get_quote_by_lance_id(telegram_id, lid)
                    item = {
                        "text": r.get("text") or "",
                        "lance_id": lid,
                        "distance": dist,
                        "closeness_pct": pct,
                        "closeness_label": label,
                        "id": meta["id"] if meta else None,
                        "added_at": meta.get("added_at") if meta else None,
                    }
                    enriched.append(item)
                return enriched, "semantic"

    rows = quotes_repo.text_search(telegram_id, query, limit=top_k)
    return rows, "keyword"
