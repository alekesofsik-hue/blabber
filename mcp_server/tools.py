"""
MCP Server — tool implementations and MCP-format schema registry.

Tools:
  • rss_search(query, source_keys, max_results)
  • top_headlines(source_key, max_results)
  • hn_top(n)
  • fetch_summary(url, max_chars)
  • compare_two_headlines(source_key_a, source_key_b)

Schema format follows MCP spec: inputSchema instead of OpenAI-style parameters.
"""

from __future__ import annotations

import logging
import random
import re
import textwrap
from typing import Any

import requests
from services import url_ingestion_service as url_ing_svc

logger = logging.getLogger("mcp_server")

# ── Curated RSS sources ───────────────────────────────────────────────────────
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
_SESSION.headers["User-Agent"] = "BlabberMCP/1.0 (+https://github.com/blabber)"

_REQ_TIMEOUT = 8  # seconds


# ── Internal helpers ──────────────────────────────────────────────────────────

def _strip_tags(html: str) -> str:
    text = html or ""
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
        if not item["link"]:
            item["link"] = _first(r"<guid[^>]*>(.*?)</guid>", raw)
        if item["title"]:
            items.append(item)
    return items


def _fetch_feed(url: str) -> list[dict[str, str]]:
    try:
        resp = _SESSION.get(url, timeout=_REQ_TIMEOUT)
        resp.raise_for_status()
        return _parse_rss(resp.text)
    except Exception as exc:
        logger.debug("rss_fetch_failed url=%s err=%s", url, exc)
        return []


# ── Public tool functions ─────────────────────────────────────────────────────

def rss_search(query: str, source_keys: list[str] | None = None, max_results: int = 5) -> dict[str, Any]:
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
    logger.info("tool_rss_search query=%r results=%d", query, len(matches))
    return {"results": matches, "total": len(matches)}


def top_headlines(source_key: str = "habr", max_results: int = 5) -> dict[str, Any]:
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
    logger.info("tool_top_headlines source=%s count=%d", source_key, len(result_items))
    return {"source": name, "items": result_items}


def hn_top(n: int = 5) -> dict[str, Any]:
    n = min(max(1, n), 10)
    try:
        resp = _SESSION.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=_REQ_TIMEOUT,
        )
        resp.raise_for_status()
        ids: list[int] = resp.json()[: n * 2]
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

    logger.info("tool_hn_top n=%d fetched=%d", n, len(stories))
    return {"stories": stories}


def fetch_summary(url: str, max_chars: int = 1500) -> dict[str, Any]:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return {"error": "URL must start with http:// or https://", "url": url}

    try:
        payload = url_ing_svc.fetch_url_document(url)
        text = payload["text"]
        truncated = len(text) > max_chars
        text = text[:max_chars]

        logger.info("tool_fetch_summary url=%s chars=%d truncated=%s", url, len(text), truncated)
        return {
            "url": payload["url"],
            "title": payload["title"],
            "text": text,
            "truncated": truncated,
        }
    except ValueError as exc:
        logger.warning("fetch_summary_failed url=%s err=%s", url, exc)
        return {"error": str(exc), "url": url}
    except Exception as exc:
        logger.warning("fetch_summary_failed url=%s err=%s", url, exc)
        return {"error": str(exc), "url": url}


# ── compare_two_headlines (та же логика, что в services/agent_tools.py) ───────

def _first_headline_from_source(source_key: str) -> dict[str, str] | None:
    entry = SOURCE_MAP.get(source_key)
    if not entry:
        return None
    name, url = entry
    items = _fetch_feed(url)
    if not items:
        return None
    it = items[0]
    return {
        "title":       it["title"][:300],
        "link":        it["link"],
        "source_name": name,
        "source_key":  source_key,
        "pubdate":     it.get("pubdate", ""),
    }


def compare_two_headlines(
    source_key_a: str | None = None,
    source_key_b: str | None = None,
) -> dict[str, Any]:
    """
    Два свежих заголовка из разных RSS-лент (для MCP; совпадает с локальным агентом).
    """
    keys = list(SOURCE_MAP.keys())

    if source_key_a is not None and source_key_b is not None:
        if source_key_a == source_key_b:
            return {"error": "Источники должны различаться."}
        if source_key_a not in SOURCE_MAP or source_key_b not in SOURCE_MAP:
            return {"error": "Неизвестный ключ источника.", "available_keys": keys}
        pair = (source_key_a, source_key_b)
    elif source_key_a is None and source_key_b is None:
        if len(keys) < 2:
            return {"error": "Недостаточно источников."}
        pair = tuple(random.sample(keys, 2))
    else:
        return {
            "error": "Укажи оба ключа или ни одного (тогда выберу два случайных).",
        }

    ha = _first_headline_from_source(pair[0])
    hb = _first_headline_from_source(pair[1])

    if not ha or not hb:
        found: list[dict[str, str]] = []
        shuffled = keys[:]
        random.shuffle(shuffled)
        for k in shuffled:
            h = _first_headline_from_source(k)
            if h:
                found.append(h)
            if len(found) >= 2:
                break
        if len(found) < 2:
            return {"error": "Не удалось получить заголовки из RSS."}
        ha, hb = found[0], found[1]

    logger.info("mcp_compare_two_headlines a=%s b=%s", ha.get("source_key"), hb.get("source_key"))
    return {
        "headline_a": ha,
        "headline_b": hb,
        "hint": (
            "Два реальных заголовка из разных лент — сравни в шутливом стиле, "
            "не выдумывай других новостей."
        ),
    }


# ── MCP Tool registry ─────────────────────────────────────────────────────────
# Schema format: MCP spec (inputSchema), not OpenAI function-calling (parameters).

TOOL_FUNCTIONS: dict[str, Any] = {
    "rss_search":             rss_search,
    "top_headlines":          top_headlines,
    "hn_top":                 hn_top,
    "fetch_summary":          fetch_summary,
    "compare_two_headlines": compare_two_headlines,
}

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "rss_search",
        "description": (
            "Ищет новости и статьи по запросу в RSS-лентах популярных источников "
            "(Хабр, 3DNews, Лента, Meduza, HN, MIT Tech и др.). "
            "Используй когда пользователь хочет найти что-то конкретное в свежих материалах."
        ),
        "inputSchema": {
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
    {
        "name": "top_headlines",
        "description": (
            "Возвращает свежие заголовки из конкретного источника. "
            "Используй когда пользователь хочет 'последние новости' с Хабра, РБК и т.д."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_key": {
                    "type": "string",
                    "description": "Ключ источника. Доступные: " + ", ".join(SOURCE_MAP.keys()),
                },
                "max_results": {
                    "type": "integer",
                    "description": "Сколько заголовков вернуть (1-10, по умолчанию 5)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "hn_top",
        "description": (
            "Возвращает топ-N историй с Hacker News прямо сейчас. "
            "Хорошо подходит для трендов в IT и стартап-тематике."
        ),
        "inputSchema": {
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
    {
        "name": "fetch_summary",
        "description": (
            "Открывает URL и возвращает читаемый текст страницы (HTML стриппинг). "
            "Используй когда пользователь прислал ссылку и хочет узнать о чём статья/страница."
        ),
        "inputSchema": {
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
    {
        "name": "compare_two_headlines",
        "description": (
            "Два самых свежих заголовка из двух разных RSS-источников — для шутливого "
            "сравнения, «битвы абсурда», псевдо-дискуссии. Ключи опциональны: "
            "если не указать — выберутся два случайных разных источника."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_key_a": {
                    "type": "string",
                    "description": (
                        "Ключ первой ленты. Доступные: " + ", ".join(SOURCE_MAP.keys())
                    ),
                },
                "source_key_b": {
                    "type": "string",
                    "description": (
                        "Ключ второй ленты (должен отличаться от первой). "
                        "Доступные: " + ", ".join(SOURCE_MAP.keys())
                    ),
                },
            },
            "required": [],
        },
    },
]
