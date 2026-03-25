"""
URL ingestion service for KB.

Responsibilities:
- fetch a public HTTP/HTTPS URL
- validate content type and size
- extract a readable title and text body
- return a normalized payload ready for KB indexing
"""

from __future__ import annotations

import html
import logging
import re
from typing import Any

import requests

logger = logging.getLogger("blabber")

FETCH_TIMEOUT_SECONDS = 10
MAX_PAGE_SIZE_BYTES = 1_000_000

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "BlabberBot/1.0 (+KB URL ingestion)"


def _strip_tags(raw_html: str) -> str:
    """Convert HTML to readable text."""
    text = raw_html or ""
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?is)<noscript[^>]*>.*?</noscript>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = re.sub(r"(?i)</div\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_title(raw_html: str, fallback_url: str) -> str:
    """Extract <title> from HTML, or fall back to the URL."""
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw_html or "")
    if not match:
        return fallback_url
    title = _strip_tags(match.group(1)).strip()
    return title or fallback_url


def fetch_url_document(url: str) -> dict[str, Any]:
    """
    Fetch and normalize a URL as a KB-ingestable document payload.

    Returns:
      {
        "url": final_url,
        "title": str,
        "text": str,
        "size_bytes": int,
        "content_type": str,
      }
    Raises:
      ValueError with a user-readable message when the URL cannot be ingested.
    """
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL должен начинаться с http:// или https://")

    try:
        response = _SESSION.get(url, timeout=FETCH_TIMEOUT_SECONDS, allow_redirects=True)
        response.raise_for_status()
    except requests.Timeout:
        raise ValueError("Сайт отвечает слишком долго. Попробуй другую ссылку.")
    except requests.RequestException as exc:
        raise ValueError(f"Не удалось загрузить страницу: {exc}")

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        raise ValueError(f"Неподдерживаемый тип содержимого: {content_type or 'unknown'}")

    body = response.content or b""
    if len(body) > MAX_PAGE_SIZE_BYTES:
        raise ValueError(f"Страница слишком большая (макс. {MAX_PAGE_SIZE_BYTES // 1024} КБ)")

    raw_text = response.text or ""
    title = _extract_title(raw_text, response.url)
    if "html" in content_type:
        body_match = re.search(r"(?is)<body[^>]*>(.*?)</body>", raw_text)
        body_html = body_match.group(1) if body_match else raw_text
        text = _strip_tags(body_html)
    else:
        text = response.text.strip()
    if not text:
        raise ValueError("Страница пустая или не содержит читаемого текста")

    payload = {
        "url": response.url,
        "title": title,
        "text": text,
        "size_bytes": len(body),
        "content_type": content_type,
    }
    logger.info(
        "kb_url_fetched",
        extra={
            "event": "kb_url_fetched",
            "url": response.url,
            "size_bytes": len(body),
            "content_type": content_type,
            "title_len": len(title),
            "text_len": len(text),
        },
    )
    return payload
