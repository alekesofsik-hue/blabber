"""
Agent commands — /agent handler for Blabber.

Commands:
  /agent              — show current status + quick-access buttons
  /agent on           — enable agent mode (incoming messages go through agent loop)
  /agent off          — disable agent mode (back to normal Balabool)
  /agent kb <url>     — save a URL page into the shared KB
  /duel               — явный запуск сравнения двух заголовков (compare_two_headlines)
  /compare_headlines  — то же, что /duel
"""

from __future__ import annotations

import logging
import os

import telebot
from telebot import types

from middleware.auth import with_user_check
from services.config_registry import get_setting
from services.agent_tools import SOURCE_MAP, hn_top, save_url_to_kb_for_user, top_headlines
from services.limiter import check_limits
from services.mcp_client import get_tools
from user_storage import get_user_voice, is_agent_enabled, is_voice_enabled, set_agent_enabled

logger = logging.getLogger("blabber")

# Сообщение в агент: заставляет модель вызвать compare_two_headlines, а не два top_headlines.
_DUEL_PROMPT_HEAD = (
    "Задача: шутливо сравни два свежих заголовка из разных новостных лент в стиле Балабола "
    "(псевдо-дискуссия, «битва абсурда», не выдумывай другие новости). "
    "ОБЯЗАТЕЛЬНО вызови ровно один раз инструмент compare_two_headlines. "
    "Не вызывай top_headlines дважды вместо него. "
)


def _build_duel_user_message(args: list[str]) -> str | None:
    """
    args — слова после команды, например ['habr', 'meduza'].
    Возвращает текст для run_agent или None если аргументы некорректны.
    """
    if len(args) == 0:
        return _DUEL_PROMPT_HEAD + "Вызови compare_two_headlines без аргументов (две случайные ленты)."
    if len(args) == 2:
        a, b = args[0], args[1]
        if a == b:
            return None  # caller sends error
        return (
            _DUEL_PROMPT_HEAD
            + f'Вызови compare_two_headlines с source_key_a="{a}" и source_key_b="{b}".'
        )
    return None  # не 0 и не 2 аргумента


def _split_command_args(message_text: str) -> list[str]:
    parts = (message_text or "").split()
    if len(parts) <= 1:
        return []
    return parts[1:]


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
                "Просто напиши что тебя интересует — сам разберусь откуда тащить инфу.\n"
                "Если хочешь сохранить страницу в базу знаний: "
                "<code>/agent kb https://example.com/article</code>\n"
                "Для явного сравнения двух заголовков из разных лент: "
                "<code>/duel</code> или <code>/compare_headlines</code> "
                "(или с ключами: <code>/duel habr meduza</code>).\n\n"
                "<i>Обычный режим без поиска: /agent off</i>",
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

        if arg in {"kb", "save_url"}:
            if len(parts) < 3:
                bot.send_message(
                    message.chat.id,
                    "🌐 <b>Как сохранить ссылку через agent</b>\n\n"
                    "Используй:\n"
                    "<code>/agent kb https://example.com/article</code>\n\n"
                    "Я добавлю страницу в твою KB тем же pipeline, что и /kb url.",
                    parse_mode="HTML",
                )
                return

            url = parts[2].strip()
            wait = bot.send_message(
                message.chat.id,
                "⏳ Агент сохраняет страницу в базу знаний...",
            )
            result = save_url_to_kb_for_user(user_id, url)
            if result.get("ok"):
                kb_note = "\n\n✅ База знаний автоматически включена." if result.get("kb_auto_enabled") else ""
                bot.edit_message_text(
                    "✅ <b>Страница сохранена в KB через agent</b>\n\n"
                    f"{result.get('message', '')}{kb_note}\n\n"
                    "Проверить KB: /kb",
                    message.chat.id,
                    wait.message_id,
                    parse_mode="HTML",
                )
            else:
                error = result.get("message") or result.get("error") or "неизвестная ошибка"
                bot.edit_message_text(
                    f"❌ Не получилось сохранить страницу в KB:\n{error}",
                    message.chat.id,
                    wait.message_id,
                )
            return

        # ── unknown subcommand → show status ──────────────────────────────────
        _send_agent_status(bot, message.chat.id, user_id)

    # ── /duel /compare_headlines — явный compare_two_headlines для агента ─────

    @bot.message_handler(commands=["duel", "compare_headlines"])
    @with_user_check(bot)
    def handle_duel(message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        maintenance = get_setting("maintenance_mode", False)
        if isinstance(maintenance, bool):
            is_maint = maintenance
        else:
            is_maint = str(maintenance).lower() in ("true", "1", "yes")
        if is_maint:
            role_weight = getattr(message, "_user", None) and message._user.get("role_weight") or 0
            if role_weight < 100:
                bot.send_message(
                    chat_id,
                    "🔧 Бот временно на техническом обслуживании. Попробуйте позже.",
                )
                return

        allowed, limit_reason = check_limits(user_id)
        if not allowed:
            bot.send_message(chat_id, limit_reason)
            return

        if not is_agent_enabled(user_id):
            bot.send_message(
                chat_id,
                "⚔️ Команда <code>/duel</code> работает в агентном режиме.\n\n"
                "Сначала включи: <code>/agent on</code>\n\n"
                "Тогда я отправлю в агент явный запрос на инструмент "
                "<code>compare_two_headlines</code> (два свежих заголовка из разных лент) "
                "и разверну шутливое сравнение.\n\n"
                "<b>Формат:</b>\n"
                "• <code>/duel</code> — случайные две ленты\n"
                "• <code>/duel habr meduza</code> — конкретные ключи (два разных). "
                "Ключи смотри в <code>/agent</code>.",
                parse_mode="HTML",
            )
            return

        args = _split_command_args(message.text)
        if len(args) not in (0, 2):
            bot.send_message(
                chat_id,
                "⚔️ Нужно <b>0</b> или <b>2</b> ключа источника.\n"
                "Примеры: <code>/duel</code> · <code>/duel habr meduza</code>",
                parse_mode="HTML",
            )
            return

        if len(args) == 2:
            if args[0] == args[1]:
                bot.send_message(
                    chat_id,
                    "⚔️ Укажи два <b>разных</b> ключа, например: <code>/duel habr meduza</code>",
                    parse_mode="HTML",
                )
                return
            for k in args:
                if k not in SOURCE_MAP:
                    known = ", ".join(sorted(SOURCE_MAP.keys()))
                    bot.send_message(
                        chat_id,
                        f"⚔️ Неизвестный ключ <code>{k}</code>.\n"
                        f"Доступные: <code>{known}</code>",
                        parse_mode="HTML",
                    )
                    return

        user_message = _build_duel_user_message(args)
        if user_message is None:
            bot.send_message(chat_id, "⚔️ Не удалось собрать запрос. Попробуй ещё раз.")
            return

        from services.agent_runner import run_agent

        bot.send_chat_action(chat_id, "typing")
        logger.info("duel_command user_id=%s args=%s", user_id, args)
        try:
            agent_response = run_agent(user_message, user_id)
        except Exception as exc:
            logger.exception("duel_agent_failed", extra={"user_id": user_id})
            agent_response = f"Агент сломался: {exc}"

        from bot import send_long_message

        send_long_message(
            chat_id,
            agent_response,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        if is_voice_enabled(user_id):
            try:
                from tts import synthesize_voice

                voice_key = get_user_voice(user_id)
                ogg_data = synthesize_voice(agent_response, voice_key=voice_key)
                bot.send_voice(chat_id, ogg_data)
            except Exception:
                pass

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
        + "🌐 Читать и пересказывать страницу по URL\n"
        + "📚 Сохранять URL-страницу в KB: <code>/agent kb https://...</code>\n"
        + "⚔️ <code>/duel</code> — два свежих заголовка из разных лент (compare_two_headlines)\n\n"
        + f"<b>Источники:</b>\n{sources_list}\n\n"
        + "<i>В agent-режиме каждое твоё сообщение обрабатывается агентом "
        + "(он сам решает, нужно ли что-то искать). Команды <code>/duel</code> и "
        + "<code>/compare_headlines</code> — явное сравнение двух лент (нужен включённый режим). "
        + "Для явного сохранения ссылки в KB: <code>/agent kb https://...</code>. "
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


