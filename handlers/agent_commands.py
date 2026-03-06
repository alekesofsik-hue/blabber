"""
Agent commands — /agent handler for Blabber.

Commands:
  /agent          — show current status + quick-access buttons
  /agent on       — enable agent mode (incoming messages go through agent loop)
  /agent off      — disable agent mode (back to normal Balabool)
"""

from __future__ import annotations

import os

import telebot
from telebot import types

from middleware.auth import with_user_check
from services.agent_tools import SOURCE_MAP, hn_top, top_headlines
from services.mcp_client import get_tools
from user_storage import is_agent_enabled, set_agent_enabled


def register_agent_handlers(bot: telebot.TeleBot) -> None:

    # ── /agent ────────────────────────────────────────────────────────────────

    @bot.message_handler(commands=["agent"])
    @with_user_check(bot)
    def handle_agent(message):
        user_id = message.from_user.id
        parts = message.text.split(maxsplit=2)

        if len(parts) < 2:
            _send_agent_status(bot, message.chat.id, user_id)
            return

        arg = parts[1].lower()

        # ── on / off ──────────────────────────────────────────────────────────
        if arg == "on":
            set_agent_enabled(user_id, True)
            bot.send_message(
                message.chat.id,
                "🕵️ <b>Agent-режим включён!</b>\n\n"
                "Теперь я — <b>Балабол-новостник</b>: сначала ищу свежие данные, "
                "потом трещу о них.\n\n"
                "Просто напиши что тебя интересует — сам разберусь откуда тащить инфу.\n\n"
                "<i>Чтобы вернуться в обычный режим: /agent off</i>",
                parse_mode="HTML",
            )
            return

        if arg == "off":
            set_agent_enabled(user_id, False)
            bot.send_message(
                message.chat.id,
                "💬 <b>Agent-режим выключен.</b>\n\n"
                "Вернулся в обычный балабольский режим. Быстро, без поисков.",
                parse_mode="HTML",
            )
            return

        # ── unknown subcommand → show status ──────────────────────────────────
        _send_agent_status(bot, message.chat.id, user_id)

    # ── Inline callbacks from status keyboard ─────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("agent_"))
    def callback_agent(call):
        user_id = call.from_user.id
        data = call.data

        if data == "agent_toggle":
            new_state = not is_agent_enabled(user_id)
            set_agent_enabled(user_id, new_state)
            label = "включён 🕵️" if new_state else "выключен 💬"
            bot.answer_callback_query(call.id, f"Agent-режим {label}")
            _refresh_agent_status(bot, call)
            return

        if data == "agent_quick_hn":
            bot.answer_callback_query(call.id)
            _quick_hn(bot, call.message.chat.id)
            return

        if data.startswith("agent_quick_"):
            source = data.split("agent_quick_", 1)[1]
            bot.answer_callback_query(call.id)
            _quick_headlines(bot, call.message.chat.id, source_key=source)
            return


# ── Status message helpers ─────────────────────────────────────────────────────

def _build_agent_status(user_id: int) -> tuple[str, types.InlineKeyboardMarkup]:
    enabled = is_agent_enabled(user_id)
    status_icon = "🕵️ включён" if enabled else "💬 выключен"

    sources_list = "\n".join(
        f"  • <code>{key}</code> — {name}"
        for key, (name, _) in SOURCE_MAP.items()
    )

    mcp_line = ""
    base_url = os.getenv("MCP_BASE_URL", "").strip()
    if base_url:
        tools = get_tools()
        if tools:
            mcp_line = f"\n<b>MCP:</b> включён ✅ (<code>{base_url}</code>, tools: {len(tools)})\n"
        else:
            mcp_line = f"\n<b>MCP:</b> настроен, но сервер не отвечает ⚠️ (<code>{base_url}</code>)\n"
    else:
        # Not configured — agent_runner will use local tool fallback
        mcp_line = "\n<b>MCP:</b> выключен (использую локальные инструменты)\n"

    text = (
        f"🤖 <b>Балабол-новостник (Agent-режим)</b>\n\n"
        f"Статус: <b>{status_icon}</b>\n\n"
        + mcp_line
        + "<b>Что умеет:</b>\n"
        + "🔍 Искать по RSS-лентам (Хабр, 3DNews, Лента, HN и др.)\n"
        + "📰 Выдавать топ заголовков по источнику\n"
        + "🔥 Показывать тренды Hacker News\n"
        + "🌐 Читать и пересказывать страницу по URL\n\n"
        + f"<b>Источники:</b>\n{sources_list}\n\n"
        + "<i>В agent-режиме каждое твоё сообщение обрабатывается агентом "
        + "(он сам решает, нужно ли что-то искать). "
        + "Кнопки ниже — быстрый просмотр заголовков без включения режима.</i>"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)
    toggle_label = "⏸ Выключить" if enabled else "✅ Включить"
    kb.add(types.InlineKeyboardButton(toggle_label, callback_data="agent_toggle"))
    kb.add(
        types.InlineKeyboardButton("📰 Хабр", callback_data="agent_quick_habr"),
        types.InlineKeyboardButton("🔥 HN",   callback_data="agent_quick_hn"),
    )
    kb.add(
        types.InlineKeyboardButton("💻 3DNews", callback_data="agent_quick_3dnews"),
        types.InlineKeyboardButton("📡 Лента", callback_data="agent_quick_lenta"),
    )
    return text, kb


def _send_agent_status(bot: telebot.TeleBot, chat_id: int, user_id: int) -> None:
    text, kb = _build_agent_status(user_id)
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)


def _refresh_agent_status(bot: telebot.TeleBot, call) -> None:
    text, kb = _build_agent_status(call.from_user.id)
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception:
        pass


# ── Quick action helpers ───────────────────────────────────────────────────────

def _quick_headlines(bot: telebot.TeleBot, chat_id: int, source_key: str = "habr") -> None:
    wait = bot.send_message(chat_id, "⏳ Достаю заголовки…")
    result = top_headlines(source_key=source_key, max_results=5)

    if "error" in result:
        bot.edit_message_text(f"❌ {result['error']}", chat_id, wait.message_id)
        return

    source_name = result.get("source", source_key)
    items = result.get("items", [])

    if not items:
        bot.edit_message_text(
            f"🤷 В «{source_name}» ничего не нашёл. Либо лента пустая, либо что-то не так.",
            chat_id, wait.message_id,
        )
        return

    lines = [f"📰 <b>Свежее с «{source_name}»:</b>\n"]
    for i, it in enumerate(items, 1):
        title = it.get("title", "—")
        link = it.get("link", "")
        desc = it.get("description", "")
        if link:
            lines.append(f"{i}. <a href=\"{link}\">{title}</a>")
        else:
            lines.append(f"{i}. {title}")
        if desc:
            lines.append(f"   <i>{desc[:120]}</i>")

    text = "\n".join(lines)
    bot.edit_message_text(text, chat_id, wait.message_id, parse_mode="HTML",
                          disable_web_page_preview=True)


def _quick_hn(bot: telebot.TeleBot, chat_id: int) -> None:
    wait = bot.send_message(chat_id, "⏳ Лезу на Hacker News…")
    result = hn_top(n=5)

    stories = result.get("stories", [])
    if "error" in result or not stories:
        err = result.get("error", "ничего не нашлось")
        bot.edit_message_text(f"❌ HN недоступен: {err}", chat_id, wait.message_id)
        return

    lines = ["🔥 <b>Hacker News — в тренде прямо сейчас:</b>\n"]
    for i, st in enumerate(stories, 1):
        url = st.get("url", "")
        title = st.get("title", "—")
        score = st.get("score", 0)
        cmts = st.get("comments", 0)
        if url:
            lines.append(f"{i}. <a href=\"{url}\">{title}</a>")
        else:
            lines.append(f"{i}. {title}")
        lines.append(f"   ⬆️ {score}  💬 {cmts}")

    bot.edit_message_text("\n".join(lines), chat_id, wait.message_id,
                          parse_mode="HTML", disable_web_page_preview=True)


