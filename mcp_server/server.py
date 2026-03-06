"""
MCP Server — HTTP API для инструментов "Балабол-новостник".

Эндпоинты:
  GET  /         — health check (статус и список доступных tools)
  GET  /tools    — список инструментов в MCP-формате (inputSchema)
  POST /call     — вызов инструмента по имени

Запуск:
  cd mcp_server
  uvicorn server:app --host 127.0.0.1 --port 51337

Или из корня проекта:
  uvicorn mcp_server.server:app --host 127.0.0.1 --port 51337
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tools import MCP_TOOLS, TOOL_FUNCTIONS

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("mcp_server")

# ── Optional token auth ───────────────────────────────────────────────────────
# Если MCP_TOKEN задан в .env — требуем его в заголовке Authorization: Bearer <token>.
# Если не задан — auth отключена (подходит для 127.0.0.1 без внешнего доступа).
MCP_TOKEN = os.getenv("MCP_TOKEN", "")


def _check_auth(request: Request) -> None:
    if not MCP_TOKEN:
        return
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {MCP_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Blabber MCP Server",
    description="MCP-совместимый HTTP сервер инструментов для Балабол-новостника",
    version="1.0.0",
)


# ── Request / Response models ─────────────────────────────────────────────────

class CallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


class CallResponse(BaseModel):
    result: Any
    error: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def health(request: Request) -> JSONResponse:
    """Health check — возвращает статус и список доступных инструментов."""
    _check_auth(request)
    return JSONResponse({
        "status": "ok",
        "server": "Blabber MCP Server",
        "version": "1.0.0",
        "tools": [t["name"] for t in MCP_TOOLS],
    })


@app.get("/tools")
async def list_tools(request: Request) -> JSONResponse:
    """Возвращает список инструментов в MCP-формате (inputSchema)."""
    _check_auth(request)
    logger.info("list_tools requested from %s", request.client)
    return JSONResponse({"tools": MCP_TOOLS})


@app.post("/call")
async def call_tool(body: CallRequest, request: Request) -> JSONResponse:
    """
    Вызвать инструмент по имени.

    Body: {"name": "rss_search", "arguments": {"query": "python MCP"}}
    Response: {"result": {...}} или {"result": null, "error": "..."}
    """
    _check_auth(request)

    fn = TOOL_FUNCTIONS.get(body.name)
    if fn is None:
        known = ", ".join(TOOL_FUNCTIONS.keys())
        logger.warning("call_tool unknown name=%s", body.name)
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tool '{body.name}'. Available: {known}",
        )

    logger.info("call_tool name=%s args=%s", body.name, json.dumps(body.arguments, ensure_ascii=False)[:200])

    try:
        result = fn(**body.arguments)
    except TypeError as exc:
        logger.warning("call_tool bad_args name=%s err=%s", body.name, exc)
        return JSONResponse({"result": None, "error": f"Bad arguments: {exc}"}, status_code=400)
    except Exception as exc:
        logger.exception("call_tool failed name=%s", body.name)
        return JSONResponse({"result": None, "error": f"Tool error: {exc}"}, status_code=500)

    logger.info("call_tool done name=%s result_len=%d", body.name, len(json.dumps(result, ensure_ascii=False)))
    return JSONResponse({"result": result})
