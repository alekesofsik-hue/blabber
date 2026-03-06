"""
Persona commands — /role

Allows users to pick a "role" (persona) for the bot.
Roles are defined in prompts.json and stored per-user in SQLite.
"""

from __future__ import annotations

import telebot
from telebot import types

from middleware.auth import with_user_check
import services.persona_service as persona_svc


def register_persona_handlers(bot: telebot.TeleBot) -> None:

    # ── /role — show current role or switch role ──────────────────────────────

    @bot.message_handler(commands=["role"])
    @with_user_check(bot)
    def handle_role(message):
        user_id = message.from_user.id
        parts = message.text.split(maxsplit=1)

        if len(parts) >= 2:
            role_key = parts[1].strip().lower()
            _switch_role(bot, message.chat.id, user_id, role_key)
        else:
            _show_role_menu(bot, message.chat.id, user_id)

    # ── Inline callback: role selected from keyboard ──────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("role_pick_"))
    def callback_role_pick(call):
        role_key = call.data[len("role_pick_"):]
        user_id = call.from_user.id
        roles = persona_svc.get_roles()

        if role_key not in roles:
            bot.answer_callback_query(call.id, "Неизвестная роль.", show_alert=True)
            return

        ok = persona_svc.set_user_role(user_id, role_key)
        if not ok:
            bot.answer_callback_query(call.id, "Не удалось переключить роль.", show_alert=True)
            return

        role = roles[role_key]
        bot.answer_callback_query(call.id, f"Роль: {role['name']}")
        try:
            current_role_key = persona_svc.get_user_role(user_id)
            bot.edit_message_text(
                _role_menu_text(current_role_key),
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=_role_keyboard(current_role_key),
            )
        except Exception:
            pass


# ── Private helpers ───────────────────────────────────────────────────────────

def _switch_role(bot: telebot.TeleBot, chat_id: int, user_id: int, role_key: str) -> None:
    roles = persona_svc.get_roles()
    if role_key not in roles:
        available = ", ".join(roles.keys())
        bot.send_message(
            chat_id,
            f"❌ Роль <b>{role_key}</b> не найдена.\n\n"
            f"Доступные роли: {available}\n"
            f"Или открой меню: /role",
            parse_mode="HTML",
        )
        return

    ok = persona_svc.set_user_role(user_id, role_key)
    if ok:
        role = roles[role_key]
        bot.send_message(
            chat_id,
            f"🎭 Роль переключена на <b>{role['name']}</b>\n"
            f"<i>{role['description']}</i>",
            parse_mode="HTML",
        )
    else:
        bot.send_message(chat_id, "❌ Не удалось переключить роль.")


def _show_role_menu(bot: telebot.TeleBot, chat_id: int, user_id: int) -> None:
    current_role_key = persona_svc.get_user_role(user_id)
    bot.send_message(
        chat_id,
        _role_menu_text(current_role_key),
        parse_mode="HTML",
        reply_markup=_role_keyboard(current_role_key),
    )


def _role_menu_text(current_role_key: str) -> str:
    roles = persona_svc.get_roles()
    current = roles.get(current_role_key, {})
    current_name = current.get("name", current_role_key)
    current_desc = current.get("description", "")
    return (
        f"🎭 <b>Роль бота</b>\n\n"
        f"Сейчас: <b>{current_name}</b>\n"
        f"<i>{current_desc}</i>\n\n"
        f"Выбери роль:"
    )


def _role_keyboard(current_role_key: str) -> types.InlineKeyboardMarkup:
    roles = persona_svc.get_roles()
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, role in roles.items():
        mark = "✅ " if key == current_role_key else ""
        kb.add(types.InlineKeyboardButton(
            f"{mark}{role['name']} — {role['description']}",
            callback_data=f"role_pick_{key}",
        ))
    return kb
