"""
Fact Of The Day service for the History Day scenario.

Primary source:
- Wikimedia On This Day API (`selected`)

Fallback source inside the same API family:
- Wikimedia On This Day API (`events`)

The service returns a normalized payload suitable for tool invocation, logging,
and prompt/context injection.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

import requests

logger = logging.getLogger("blabber")

WIKIMEDIA_API_BASE = "https://api.wikimedia.org/feed/v1/wikipedia"
DEFAULT_LANGUAGE = "en"
DEFAULT_SCOPE = "general_history"
REQUEST_TIMEOUT = 10

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "BlabberBot/1.0 (+https://github.com/blabber)"


def normalize_requested_date(date: str = "", *, now: datetime | None = None) -> dict[str, Any]:
    """
    Normalize supported date formats into `MM-DD`.

    Supported formats:
    - empty string -> today's UTC date
    - MM-DD
    - MM/DD
    - YYYY-MM-DD
    """
    now = now or datetime.now(UTC)
    raw = (date or "").strip()
    if not raw:
        return {
            "ok": True,
            "month": now.month,
            "day": now.day,
            "date": f"{now.month:02d}-{now.day:02d}",
            "source": "today_utc",
        }

    mm_dd_match = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})", raw)
    if mm_dd_match:
        month = int(mm_dd_match.group(1))
        day = int(mm_dd_match.group(2))
    else:
        iso_match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", raw)
        if not iso_match:
            return {
                "ok": False,
                "error": "unsupported_date_format",
                "message": "Поддерживаются форматы MM-DD, MM/DD или YYYY-MM-DD",
                "date": raw,
            }
        month = int(iso_match.group(2))
        day = int(iso_match.group(3))

    try:
        datetime(2024, month, day)
    except ValueError:
        return {
            "ok": False,
            "error": "invalid_date",
            "message": "Некорректная дата для исторического сценария",
            "date": raw,
        }

    return {
        "ok": True,
        "month": month,
        "day": day,
        "date": f"{month:02d}-{day:02d}",
        "source": "user_input",
    }


def _extract_page_data(item: dict[str, Any]) -> dict[str, str]:
    pages = item.get("pages") or []
    if not pages:
        return {
            "page_title": "",
            "page_url": "",
            "page_description": "",
            "thumbnail_url": "",
            "image_url": "",
        }
    page = pages[0] or {}
    title = str(
        ((page.get("titles") or {}).get("normalized"))
        or page.get("normalizedtitle")
        or page.get("title")
        or ""
    )
    url = str((((page.get("content_urls") or {}).get("desktop") or {}).get("page")) or "")
    return {
        "page_title": title,
        "page_url": url,
        "page_description": str(page.get("description") or ""),
        "thumbnail_url": str(((page.get("thumbnail") or {}).get("source")) or ""),
        "image_url": str(((page.get("originalimage") or {}).get("source")) or ""),
    }


def _fetch_payload(*, kind: str, month: int, day: int, language: str) -> dict[str, Any]:
    url = f"{WIKIMEDIA_API_BASE}/{language}/onthisday/{kind}/{month:02d}/{day:02d}"
    response = _SESSION.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Unexpected Wikimedia payload shape")
    return payload


def _normalize_fact_item(
    *,
    item: dict[str, Any],
    requested_date: str,
    language: str,
    origin_kind: str,
    fallback_used: bool,
    fallback_reason: str | None,
) -> dict[str, Any]:
    page_data = _extract_page_data(item)
    return {
        "ok": True,
        "scope": DEFAULT_SCOPE,
        "language": language,
        "date": requested_date,
        "year": item.get("year"),
        "event": str(item.get("text") or "").strip(),
        "source_title": page_data["page_title"],
        "source_url": page_data["page_url"],
        **page_data,
        "origin_kind": origin_kind,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
    }


def _has_image(fact_item: dict[str, Any]) -> bool:
    return bool(str(fact_item.get("image_url") or "").strip() or str(fact_item.get("thumbnail_url") or "").strip())


def _pick_fact_with_image(
    *,
    items: list[dict[str, Any]],
    requested_date: str,
    language: str,
    origin_kind: str,
    fallback_used: bool,
    fallback_reason: str | None,
) -> dict[str, Any] | None:
    for item in items:
        normalized = _normalize_fact_item(
            item=item,
            requested_date=requested_date,
            language=language,
            origin_kind=origin_kind,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )
        if _has_image(normalized):
            return normalized
    return None


def get_fact_of_the_day(date: str = "", language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """
    Return a normalized historical fact for the requested date.

    The current Sprint 4 decision is to support only general history facts.
    """
    normalized_date = normalize_requested_date(date)
    if not normalized_date["ok"]:
        return {
            "ok": False,
            "scope": DEFAULT_SCOPE,
            "language": language,
            "date": normalized_date.get("date", date),
            "error": normalized_date["error"],
            "message": normalized_date["message"],
            "fallback_used": False,
            "fallback_reason": None,
        }

    month = int(normalized_date["month"])
    day = int(normalized_date["day"])
    requested_date = str(normalized_date["date"])

    try:
        selected_payload = _fetch_payload(kind="selected", month=month, day=day, language=language)
        selected_items = selected_payload.get("selected") or []
        selected_fact = _pick_fact_with_image(
            items=selected_items,
            requested_date=requested_date,
            language=language,
            origin_kind="selected",
            fallback_used=False,
            fallback_reason=None,
        )
        if selected_fact:
            logger.info("history_day_fact_loaded date=%s kind=selected", requested_date)
            return selected_fact
    except Exception as exc:
        logger.warning("history_day_fact_selected_failed date=%s err=%s", requested_date, str(exc)[:200])

    try:
        events_payload = _fetch_payload(kind="events", month=month, day=day, language=language)
        events = events_payload.get("events") or []
        events_fact = _pick_fact_with_image(
            items=events,
            requested_date=requested_date,
            language=language,
            origin_kind="events",
            fallback_used=True,
            fallback_reason="selected_unavailable_empty_or_without_image",
        )
        if events_fact:
            logger.info("history_day_fact_loaded date=%s kind=events", requested_date)
            return events_fact
    except Exception as exc:
        logger.warning("history_day_fact_events_failed date=%s err=%s", requested_date, str(exc)[:200])

    return {
        "ok": False,
        "scope": DEFAULT_SCOPE,
        "language": language,
        "date": requested_date,
        "error": "history_fact_with_image_unavailable",
        "message": "Не удалось получить исторический факт дня с изображением из внешнего источника",
        "fallback_used": True,
        "fallback_reason": "wikimedia_unavailable_or_no_image",
    }
