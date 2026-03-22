"""
Agent runner — "Балабол-новостник" agent loop.

Architecture (Variant D):
  - LLM loop: "think → tool_call → observation → final answer"
  - Max MAX_STEPS tool calls per session to prevent runaway loops
  - Uses OpenAI function-calling (works with any OpenAI-compatible backend)
  - Falls back to PROXY_API_KEY (OpenRouter/DeepSeek) if OPENAI_API_KEY absent
  - memory.json: per-user file export of the agent session (ДЗ artifact),
    fully separate from Blabber's SQLite memory.
    The file is written after each session but never read back —
    the real persistent memory lives in SQLite (context_service / profile_service).
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

import services.mcp_client as mcp_client
from services.agent_tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

logger = logging.getLogger("blabber")

# ── Configuration ─────────────────────────────────────────────────────────────

MAX_STEPS = 5           # max tool calls per agent run
AGENT_MODEL_ENV = "AGENT_MODEL"
AGENT_MEMORY_DIR = Path("agent_memory")   # per-user memory.json files live here

AGENT_SYSTEM = (
    "Ты — Балабол, говорливый и шутливый AI-ассистент. "
    "У тебя есть инструменты для поиска свежих новостей и статей в интернете. "
    "Если просят сравнить два мира новостей, «битву абсурда», псевдо-дискуссию "
    "между лентами — вызывай compare_two_headlines (один вызов), потом развивай "
    "юмор на основе **реальных** заголовков из ответа инструмента. "
    "Когда пользователь спрашивает о новостях, трендах, свежих статьях — "
    "используй инструменты, чтобы найти реальные данные, а потом болтай о них "
    "с юмором и азартом. Цитируй заголовки, шути, отвлекайся, трепись — "
    "но основу бери из свежих данных, которые получил от инструментов. "
    "Если инструменты ничего не нашли или недоступны — честно скажи об этом, "
    "но не скучно, а как настоящий балабол.\n\n"
    "ВАЖНО: когда упоминаешь конкретную статью или новость из результатов инструментов, "
    "вставляй ссылку прямо в текст в формате Markdown: [заголовок](url). "
    "Не выноси ссылки отдельным списком в конце — вплетай их в речь органично, "
    "как говорун, который тычет пальцем в экран и говорит «вот, смотри сам»."
)


# ── OpenAI client (function-calling capable) ──────────────────────────────────

def _make_client() -> tuple[OpenAI, str]:
    """
    Return (OpenAI client, model_name).
    Priority: OPENAI_API_KEY → PROXY_API_KEY (OpenRouter/DeepSeek with FC support).
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    proxy_key = os.getenv("PROXY_API_KEY")
    model_override = os.getenv(AGENT_MODEL_ENV)

    if openai_key:
        model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return OpenAI(api_key=openai_key), model

    if proxy_key:
        # OpenRouter via proxyapi.ru — DeepSeek supports function calling
        model = model_override or "deepseek/deepseek-chat"
        return OpenAI(
            api_key=proxy_key,
            base_url="https://api.proxyapi.ru/openrouter/v1",
        ), model

    raise ValueError(
        "Для agent-режима нужен OPENAI_API_KEY или PROXY_API_KEY в .env. "
        "Добавь один из ключей и перезапусти бота."
    )


# ── memory.json helpers (ДЗ artifact) ─────────────────────────────────────────

def _memory_path(user_id: int) -> Path:
    AGENT_MEMORY_DIR.mkdir(exist_ok=True)
    return AGENT_MEMORY_DIR / f"memory_{user_id}.json"


def _load_memory(user_id: int) -> dict[str, Any]:
    path = _memory_path(user_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"user_id": user_id, "sessions": []}


def _save_memory(user_id: int, memory: dict[str, Any]) -> None:
    try:
        path = _memory_path(user_id)
        path.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("agent_memory_save_failed user_id=%s err=%s", user_id, exc)


def _append_session(user_id: int, session: dict[str, Any]) -> None:
    """Append a completed agent session to the user's memory.json."""
    memory = _load_memory(user_id)
    sessions: list = memory.setdefault("sessions", [])
    sessions.append(session)
    # Keep last 50 sessions to avoid unbounded growth
    if len(sessions) > 50:
        memory["sessions"] = sessions[-50:]
    _save_memory(user_id, memory)


# ── Source extraction from tool results ──────────────────────────────────────

def _extract_sources(tool_name: str, result_json: str) -> list[dict[str, str]]:
    """
    Parse a tool result JSON and extract {"title", "url"} pairs.
    Returns an empty list if the tool doesn't produce URLs or parsing fails.
    """
    try:
        data = json.loads(result_json)
    except Exception:
        return []

    sources: list[dict[str, str]] = []

    if tool_name == "rss_search":
        for item in data.get("results", []):
            url = item.get("link", "").strip()
            title = item.get("title", "").strip()
            if url and url.startswith("http"):
                sources.append({"title": title or url, "url": url})

    elif tool_name == "top_headlines":
        for item in data.get("items", []):
            url = item.get("link", "").strip()
            title = item.get("title", "").strip()
            if url and url.startswith("http"):
                sources.append({"title": title or url, "url": url})

    elif tool_name == "hn_top":
        for story in data.get("stories", []):
            url = story.get("url", "").strip()
            title = story.get("title", "").strip()
            if url and url.startswith("http"):
                sources.append({"title": title or url, "url": url})

    elif tool_name == "fetch_summary":
        url = data.get("url", "").strip()
        if url and url.startswith("http"):
            sources.append({"title": url, "url": url})

    elif tool_name == "compare_two_headlines":
        for key in ("headline_a", "headline_b"):
            h = data.get(key) or {}
            if not isinstance(h, dict):
                continue
            url = (h.get("link") or "").strip()
            title = (h.get("title") or "").strip()
            if url and url.startswith("http"):
                sources.append({"title": title or url, "url": url})

    return sources


def _build_sources_block(sources: list[dict[str, str]]) -> str:
    """
    Build a «📎 Источники» footer block from a deduplicated list of sources.
    Returns an empty string if sources is empty.
    """
    if not sources:
        return ""

    # Deduplicate by URL, preserve insertion order
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for s in sources:
        if s["url"] not in seen:
            seen.add(s["url"])
            unique.append(s)

    lines = ["\n\n📎 <b>Источники:</b>"]
    for s in unique:
        title = s["title"][:80] + ("…" if len(s["title"]) > 80 else "")
        lines.append(f'• <a href="{s["url"]}">{title}</a>')
    return "\n".join(lines)


# ── Tool call dispatcher ──────────────────────────────────────────────────────

def _dispatch_tool(name: str, arguments: str) -> str:
    """
    Call the named tool and return a JSON string result.

    Transport priority:
      1. MCP server (HTTP) — if MCP_BASE_URL is configured and server responds.
      2. Local Python functions — fallback when MCP is unavailable/unconfigured.
    """
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        args = {}

    # ── Try MCP server first ──────────────────────────────────────────────────
    if mcp_client.is_configured():
        result = mcp_client.call_tool(name, args)
        # Propagate to local fallback only on "server unavailable" errors
        if "error" not in result or not any(
            phrase in result["error"]
            for phrase in ("MCP server unavailable", "MCP server timeout", "MCP_BASE_URL is not")
        ):
            logger.info("dispatch_tool transport=mcp name=%s", name)
            return json.dumps(result, ensure_ascii=False)
        logger.warning("dispatch_tool mcp_failed name=%s err=%s — falling back to local", name, result["error"])

    # ── Local fallback ────────────────────────────────────────────────────────
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**args)
    except TypeError as exc:
        result = {"error": f"Bad arguments for {name}: {exc}"}
    except Exception as exc:
        result = {"error": f"Tool {name} failed: {exc}"}
    logger.info("dispatch_tool transport=local name=%s", name)
    return json.dumps(result, ensure_ascii=False)


# ── Main agent loop ───────────────────────────────────────────────────────────

def run_agent(user_message: str, user_id: int) -> str:
    """
    Run the agent loop for a single user message.

    Steps:
      1. Call LLM with tools; if it requests a tool call → dispatch → re-call LLM.
      2. Repeat up to MAX_STEPS times.
      3. Collect source URLs from all tool results, append deduplicated «Источники» block.
      4. Export session (incl. sources) to memory.json (ДЗ artifact).
      5. Return final text answer with sources footer.

    Args:
        user_message: The user's text message.
        user_id:      Telegram user ID (for memory.json scoping).

    Returns:
        Final text response from the agent, with «📎 Источники» block appended if any.
    """
    t_start = time.monotonic()

    try:
        client, model = _make_client()
    except ValueError as exc:
        return str(exc)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": AGENT_SYSTEM},
        {"role": "user",   "content": user_message},
    ]

    session: dict[str, Any] = {
        "ts":           datetime.now(UTC).isoformat(),
        "user_message": user_message,
        "model":        model,
        "steps":        [],
        "sources":      [],
        "final":        "",
    }

    # Accumulate sources across all tool calls in this session
    all_sources: list[dict[str, str]] = []
    final_answer = ""

    for step in range(MAX_STEPS):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.8,
                max_tokens=2000,
            )
        except Exception as exc:
            logger.warning("agent_llm_call_failed step=%d err=%s", step, exc)
            error_msg = str(exc)
            session["steps"].append({"step": step, "error": error_msg})
            final_answer = (
                f"Упс, что-то пошло не так на шаге {step + 1}: {error_msg}\n"
                "Попробуй переформулировать запрос или переключись в обычный режим /agent off"
            )
            break

        choice = response.choices[0]
        msg = choice.message
        step_log: dict[str, Any] = {"step": step}

        # ── No tool call → final answer ───────────────────────────────────────
        if not msg.tool_calls:
            final_answer = msg.content or ""
            step_log["type"] = "final"
            step_log["answer_len"] = len(final_answer)
            session["steps"].append(step_log)
            logger.info("agent_final_answer step=%d user_id=%s len=%d", step, user_id, len(final_answer))
            break

        # ── Process tool calls ────────────────────────────────────────────────
        step_log["type"] = "tool_calls"
        step_log["calls"] = []

        # Append the assistant message with tool_calls to conversation
        messages.append({
            "role":       "assistant",
            "content":    msg.content,
            "tool_calls": [
                {
                    "id":       tc.id,
                    "type":     "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            tool_args = tc.function.arguments
            logger.info("agent_tool_call step=%d tool=%s user_id=%s", step, tool_name, user_id)

            observation = _dispatch_tool(tool_name, tool_args)

            # ── Collect sources from this tool result ─────────────────────────
            step_sources = _extract_sources(tool_name, observation)
            all_sources.extend(step_sources)

            # Append tool result
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      observation,
            })

            step_log["calls"].append({
                "tool":       tool_name,
                "args":       tool_args,
                "result_len": len(observation),
                "sources":    step_sources,
            })

        session["steps"].append(step_log)

    else:
        # Exhausted MAX_STEPS without a final answer — ask LLM to summarise
        logger.warning("agent_max_steps_reached user_id=%s", user_id)
        try:
            messages.append({
                "role":    "user",
                "content": "Подведи итог того, что ты нашёл, кратко и по-балабольски.",
            })
            fallback = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.8,
                max_tokens=1000,
            )
            final_answer = fallback.choices[0].message.content or "Ничего не нашёл, не обессудь!"
        except Exception:
            final_answer = "Слишком много шагов — запутался! Попробуй спросить по-другому."

    # ── Append sources block ──────────────────────────────────────────────────
    sources_block = _build_sources_block(all_sources)
    if sources_block:
        final_answer = final_answer + sources_block

    dt_ms = int((time.monotonic() - t_start) * 1000)
    session["final"] = final_answer
    session["sources"] = all_sources
    session["duration_ms"] = dt_ms

    # Export to memory.json (ДЗ artifact — does not affect bot UX)
    _append_session(user_id, session)

    logger.info(
        "agent_run_complete user_id=%s steps=%d sources=%d duration_ms=%d final_len=%d",
        user_id, len(session["steps"]), len(all_sources), dt_ms, len(final_answer),
    )
    return final_answer
