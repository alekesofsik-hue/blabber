"""
Profile commands — /remember, /profile.

Lets users store personal facts that are injected into every LLM request
(long-term memory D).  The bot "remembers" preferences, names, project
context etc. across sessions and model switches.
"""

from __future__ import annotations

import telebot
from telebot import types

from middleware.auth import with_user_check
import services.profile_service as profile_svc


def register_profile_handlers(bot: telebot.TeleBot) -> None:

    # ── /remember ────────────────────────────────────────────────────────────

    @bot.message_handler(commands=["remember"])
    @with_user_check(bot)
    def handle_remember(message):
        user_id = message.from_user.id
        parts = message.text.split(maxsplit=1)

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "🧠 <b>Как пользоваться /remember</b>\n\n"
                "Напиши факт о себе — я запомню его навсегда "
                "(даже после перезапуска и смены модели).\n\n"
                "<b>Примеры:</b>\n"
                "/remember Меня зовут Алексей\n"
                "/remember Предпочитаю краткие ответы\n"
                "/remember Мой проект — Telegram-бот на Python\n"
                "/remember Не использовать сложные термины\n\n"
                "Посмотреть и удалить факты: /profile",
                parse_mode="HTML",
            )
            return

        fact = parts[1].strip()
        ok, msg = profile_svc.add_fact(user_id, fact)
        emoji = "🧠" if ok else "❌"
        bot.send_message(message.chat.id, f"{emoji} {msg}")

    # ── /profile ──────────────────────────────────────────────────────────────

    @bot.message_handler(commands=["profile"])
    @with_user_check(bot)
    def handle_profile(message):
        _send_profile(bot, message.chat.id, message.from_user.id)

    # ── Callback: delete individual fact ──────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("profile_del_"))
    def callback_profile_del(call):
        user_id = call.from_user.id
        try:
            profile_id = int(call.data.split("_", 2)[2])
        except (IndexError, ValueError):
            bot.answer_callback_query(call.id, "Ошибка.")
            return

        ok, msg = profile_svc.delete_fact_by_id(user_id, profile_id)
        bot.answer_callback_query(call.id, msg)
        _refresh_profile(bot, call)

    @bot.callback_query_handler(func=lambda c: c.data == "profile_clear_all")
    def callback_profile_clear_all(call):
        profile_svc.clear_facts(call.from_user.id)
        bot.answer_callback_query(call.id, "Всё забыл!")
        _refresh_profile(bot, call)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_profile_message(user_id: int) -> tuple[str, types.InlineKeyboardMarkup | None]:
    facts = profile_svc.get_facts_with_ids(user_id)
    if not facts:
        text = (
            "🧠 <b>Профиль пуст</b>\n\n"
            "Я ещё ничего не знаю о тебе.\n"
            "Расскажи — и я буду учитывать это в каждом ответе!\n\n"
            "<b>Примеры:</b>\n"
            "/remember Меня зовут Алексей\n"
            "/remember Я предпочитаю краткие ответы"
        )
        return text, None

    count = len(facts)
    text = f"🧠 <b>Профиль</b> ({count}/{profile_svc.MAX_FACTS} фактов)\n\n"
    for item in facts:
        text += f"• {item['fact']}\n"

    if count >= profile_svc.MAX_FACTS:
        text += f"\n⚠️ Достигнут лимит ({profile_svc.MAX_FACTS} фактов).\n"

    text += "\nНажми ❌ рядом с фактом чтобы удалить:"

    kb = types.InlineKeyboardMarkup(row_width=1)
    for item in facts:
        label = item["fact"]
        short = label[:40] + ("…" if len(label) > 40 else "")
        kb.add(types.InlineKeyboardButton(
            f"❌ {short}",
            callback_data=f"profile_del_{item['id']}",
        ))
    kb.add(types.InlineKeyboardButton("🗑 Удалить всё", callback_data="profile_clear_all"))

    return text, kb


def _send_profile(bot: telebot.TeleBot, chat_id: int, user_id: int) -> None:
    text, kb = _build_profile_message(user_id)
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)


def _refresh_profile(bot: telebot.TeleBot, call) -> None:
    text, kb = _build_profile_message(call.from_user.id)
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
