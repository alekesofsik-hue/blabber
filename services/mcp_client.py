"""
MCP Client — HTTP клиент для вызова инструментов через MCP-сервер.

Настройка через .env:
  MCP_BASE_URL=http://127.0.0.1:51337   (URL MCP-сервера)
  MCP_TOKEN=                            (Bearer-токен, если сервер требует auth; пусто = без auth)
  MCP_TIMEOUT=10                        (таймаут HTTP-запроса в секундах)

Если MCP_BASE_URL не задан — клиент работает в "offline"-режиме и сразу
возвращает ошибку, что позволяет agent_runner сделать fallback на локальные функции.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger("blabber")

_MCP_BASE_URL = os.getenv("MCP_BASE_URL", "").rstrip("/")
_MCP_TOKEN = os.getenv("MCP_TOKEN", "")
_MCP_TIMEOUT = int(os.getenv("MCP_TIMEOUT", "10"))

_SESSION = requests.Session()
_SESSION.headers.update({"Content-Type": "application/json"})
if _MCP_TOKEN:
    _SESSION.headers["Authorization"] = f"Bearer {_MCP_TOKEN}"


def is_configured() -> bool:
    """Возвращает True, если MCP_BASE_URL задан в окружении."""
    return bool(_MCP_BASE_URL)


def get_tools() -> list[dict[str, Any]]:
    """
    Получить список инструментов с MCP-сервера (GET /tools).

    Returns:
        Список tool-объектов в MCP-формате (с inputSchema).
        Пустой список при ошибке или если сервер не настроен.
    """
    if not _MCP_BASE_URL:
        return []
    try:
        resp = _SESSION.get(f"{_MCP_BASE_URL}/tools", timeout=_MCP_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("tools", [])
    except Exception as exc:
        logger.warning("mcp_client.get_tools failed: %s", exc)
        return []


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Вызвать инструмент на MCP-сервере (POST /call).

    Args:
        name:      Имя инструмента (например, "rss_search").
        arguments: Словарь аргументов.

    Returns:
        Словарь-результат из поля "result" ответа.
        При ошибке — {"error": "<описание>"}.
    """
    if not _MCP_BASE_URL:
        return {"error": "MCP_BASE_URL is not configured"}

    payload = {"name": name, "arguments": arguments}
    try:
        resp = _SESSION.post(
            f"{_MCP_BASE_URL}/call",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=_MCP_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()

        if body.get("error"):
            logger.warning("mcp_client.call_tool server_error name=%s err=%s", name, body["error"])
            return {"error": body["error"]}

        return body.get("result") or {}

    except requests.exceptions.ConnectionError as exc:
        logger.warning("mcp_client.call_tool connection_error name=%s err=%s", name, exc)
        return {"error": f"MCP server unavailable: {exc}"}
    except requests.exceptions.Timeout:
        logger.warning("mcp_client.call_tool timeout name=%s timeout=%ds", name, _MCP_TIMEOUT)
        return {"error": f"MCP server timeout after {_MCP_TIMEOUT}s"}
    except Exception as exc:
        logger.warning("mcp_client.call_tool failed name=%s err=%s", name, exc)
        return {"error": str(exc)}
