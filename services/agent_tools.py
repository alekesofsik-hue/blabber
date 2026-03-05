"""
Agent tools — "Балабол-новостник" toolkit.

Four tools available to the agent:
  • rss_search(query, max_results)    — full-text search across curated RSS feeds
  • top_headlines(source, max_results) — latest N headlines from a source
  • hn_top(n)                          — top N stories from Hacker News (API)
  • fetch_summary(url, max_chars)      — fetch a URL and return extracted text
"""

from __future__ import annotations

import logging
import re
import textwrap
from typing import Any

import requests

logger = logging.getLogger("blabber")

# ── Curated RSS sources ───────────────────────────────────────────────────────
# Each entry: (key, display_name, feed_url)
RSS_SOURCES: list[tuple[str, str, str]] = [
    ("habr",     "Хабр (IT)",              "https://habr.com/ru/rss/articles/?fl=ru"),
    ("habr_en",  "Habr (English)",          "https://habr.com/en/rss/articles/?fl=en"),
    ("3dnews",   "3DNews (IT/гаджеты)",     "https://3dnews.ru/news/rss/"),
    ("meduza",   "Meduza",                  "https://meduza.io/rss/all"),
    ("lenta",    "Лента.ру",               "https://lenta.ru/rss/news"),
    ("rbc",      "РБК Новости",            "https://rbc.ru/rss/news"),
    ("bbc_ru",   "BBC Россия",             "https://feeds.bbci.co.uk/russian/rss.xml"),
    ("tass",     "ТАСС",                   "https://tass.ru/rss/v2.xml"),
    ("hn",       "Hacker News",            "https://hnrss.org/frontpage"),
    ("mit_tech", "MIT Tech Review",         "https://www.technologyreview.com/feed/"),
]

SOURCE_MAP: dict[str, tuple[str, str]] = {key: (name, url) for key, name, url in RSS_SOURCES}

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "BlabberBot/1.0 (+https://github.com/blabber)"

_REQ_TIMEOUT = 8  # seconds


# ── Internal helpers ──────────────────────────────────────────────────────────

def _strip_tags(html: str) -> str:
    """Strip HTML/XML tags (incl. CDATA) and normalize whitespace."""
    text = html or ""
    # Unwrap CDATA sections first
    text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_rss(xml: str) -> list[dict[str, str]]:
    """
    Minimal RSS parser (no deps).
    Returns list of {"title", "link", "description", "pubdate"}.
    """
    items: list[dict[str, str]] = []

    def _first(pattern: str, text: str) -> str:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return _strip_tags(m.group(1)) if m else ""

    raw_items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL | re.IGNORECASE)
    for raw in raw_items:
        item: dict[str, str] = {
            "title":       _first(r"<title[^>]*>(.*?)</title>", raw),
            "link":        _first(r"<link[^>]*>(.*?)</link>", raw),
            "description": _first(r"<description[^>]*>(.*?)</description>", raw),
            "pubdate":     _first(r"<pubDate[^>]*>(.*?)</pubDate>", raw),
        }
        # Some feeds use <guid> as link
        if not item["link"]:
            item["link"] = _first(r"<guid[^>]*>(.*?)</guid>", raw)
        if item["title"]:
            items.append(item)
    return items


def _fetch_feed(url: str) -> list[dict[str, str]]:
    """Fetch and parse a single RSS feed. Returns [] on any error."""
    try:
        resp = _SESSION.get(url, timeout=_REQ_TIMEOUT)
        resp.raise_for_status()
        return _parse_rss(resp.text)
    except Exception as exc:
        logger.debug("rss_fetch_failed url=%s err=%s", url, exc)
        return []


# ── Public tool functions ─────────────────────────────────────────────────────

def rss_search(query: str, source_keys: list[str] | None = None, max_results: int = 5) -> dict[str, Any]:
    """
    Full-text search across one or more RSS feeds.

    Args:
        query:       Search terms (space-separated, case-insensitive).
        source_keys: List of SOURCE_MAP keys to search. None = all sources.
        max_results: Max number of results to return.

    Returns:
        {"results": [{"title", "link", "description", "source", "pubdate"}], "total": int}
    """
    query = query.strip()
    if not query:
        return {"results": [], "total": 0, "error": "empty query"}

    tokens = [t.lower() for t in query.split() if t]
    sources = source_keys or list(SOURCE_MAP.keys())

    matches: list[dict[str, str]] = []
    for key in sources:
        entry = SOURCE_MAP.get(key)
        if not entry:
            continue
        name, url = entry
        items = _fetch_feed(url)
        for item in items:
            haystack = (item["title"] + " " + item["description"]).lower()
            if any(t in haystack for t in tokens):
                matches.append({
                    "title":       item["title"][:200],
                    "link":        item["link"],
                    "description": textwrap.shorten(item["description"], 300, placeholder="…"),
                    "pubdate":     item["pubdate"],
                    "source":      name,
                })
            if len(matches) >= max_results * 3:
                break

    matches = matches[:max_results]
    logger.info("agent_tool_rss_search query=%r results=%d", query, len(matches))
    return {"results": matches, "total": len(matches)}


def top_headlines(source_key: str = "habr", max_results: int = 5) -> dict[str, Any]:
    """
    Get the latest N headlines from a specific RSS source.

    Args:
        source_key:  Key from SOURCE_MAP (e.g. 'habr', 'vc', 'lenta').
        max_results: How many items to return.

    Returns:
        {"source": str, "items": [{"title", "link", "description", "pubdate"}]}
    """
    entry = SOURCE_MAP.get(source_key)
    if not entry:
        available = ", ".join(SOURCE_MAP.keys())
        return {"error": f"Unknown source '{source_key}'. Available: {available}"}

    name, url = entry
    items = _fetch_feed(url)
    result_items = [
        {
            "title":       it["title"][:200],
            "link":        it["link"],
            "description": textwrap.shorten(it["description"], 300, placeholder="…"),
            "pubdate":     it["pubdate"],
        }
        for it in items[:max_results]
    ]
    logger.info("agent_tool_top_headlines source=%s count=%d", source_key, len(result_items))
    return {"source": name, "items": result_items}


def hn_top(n: int = 5) -> dict[str, Any]:
    """
    Get top N stories from Hacker News (via official Firebase API).

    Args:
        n: How many stories to return (max 10).

    Returns:
        {"stories": [{"title", "url", "score", "comments", "by", "id"}]}
    """
    n = min(max(1, n), 10)
    try:
        resp = _SESSION.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=_REQ_TIMEOUT,
        )
        resp.raise_for_status()
        ids: list[int] = resp.json()[:n * 2]
    except Exception as exc:
        logger.warning("hn_top_ids_failed err=%s", exc)
        return {"error": f"HN API unavailable: {exc}", "stories": []}

    stories: list[dict[str, Any]] = []
    for sid in ids:
        if len(stories) >= n:
            break
        try:
            sr = _SESSION.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                timeout=_REQ_TIMEOUT,
            )
            sr.raise_for_status()
            item = sr.json()
            if not item or item.get("type") != "story":
                continue
            stories.append({
                "title":    item.get("title", "")[:200],
                "url":      item.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                "score":    item.get("score", 0),
                "comments": item.get("descendants", 0),
                "by":       item.get("by", ""),
                "id":       sid,
            })
        except Exception as exc:
            logger.debug("hn_item_failed id=%s err=%s", sid, exc)

    logger.info("agent_tool_hn_top n=%d fetched=%d", n, len(stories))
    return {"stories": stories}


def fetch_summary(url: str, max_chars: int = 1500) -> dict[str, Any]:
    """
    Fetch a URL and extract readable text (stripping HTML).

    Args:
        url:       HTTP/HTTPS URL to fetch.
        max_chars: Max characters of extracted text to return.

    Returns:
        {"url": str, "text": str, "truncated": bool}
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return {"error": "URL must start with http:// or https://", "url": url}

    try:
        resp = _SESSION.get(url, timeout=_REQ_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "html" not in content_type and "text" not in content_type:
            return {"error": f"Non-text content: {content_type}", "url": url}

        text = _strip_tags(resp.text)
        # collapse runs of whitespace / blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        text = text.strip()

        truncated = len(text) > max_chars
        text = text[:max_chars]

        logger.info("agent_tool_fetch_summary url=%s chars=%d truncated=%s", url, len(text), truncated)
        return {"url": url, "text": text, "truncated": truncated}

    except Exception as exc:
        logger.warning("fetch_summary_failed url=%s err=%s", url, exc)
        return {"error": str(exc), "url": url}


# ── Tool registry — used by agent_runner ─────────────────────────────────────

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "rss_search",
            "description": (
                "Ищет новости и статьи по запросу в RSS-лентах популярных источников "
                "(Хабр, 3DNews, Лента, Meduza, HN, MIT Tech и др.). "
                "Используй когда пользователь хочет найти что-то конкретное в свежих материалах."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос (ключевые слова через пробел)",
                    },
                    "source_keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Ключи источников для поиска. Доступные: "
                            + ", ".join(SOURCE_MAP.keys())
                            + ". Если не указать — ищет везде."
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Максимум результатов (1-10, по умолчанию 5)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_headlines",
            "description": (
                "Возвращает свежие заголовки из конкретного источника. "
                "Используй когда пользователь хочет 'последние новости' с Хабра, VC, РБК и т.д."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source_key": {
                        "type": "string",
                        "description": (
                            "Ключ источника. Доступные: "
                            + ", ".join(SOURCE_MAP.keys())
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Сколько заголовков вернуть (1-10, по умолчанию 5)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hn_top",
            "description": (
                "Возвращает топ-N историй с Hacker News прямо сейчас. "
                "Хорошо подходит для трендов в IT и стартап-тематике."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "Сколько историй вернуть (1-10, по умолчанию 5)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_summary",
            "description": (
                "Открывает URL и возвращает читаемый текст страницы (HTML стриппинг). "
                "Используй когда пользователь прислал ссылку и хочет узнать о чём статья/страница."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "HTTP/HTTPS URL для загрузки",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Максимум символов извлечённого текста (по умолч. 1500)",
                    },
                },
                "required": ["url"],
            },
        },
    },
]

TOOL_FUNCTIONS: dict[str, Any] = {
    "rss_search":    rss_search,
    "top_headlines": top_headlines,
    "hn_top":        hn_top,
    "fetch_summary": fetch_summary,
}
