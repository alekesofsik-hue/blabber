"""
Admin commands — Telegram admin interface with inline keyboard.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from typing import Any

import telebot
from telebot import types

from database import get_connection
from database.engine import get_db_path
from middleware.auth import require_role, require_role_callback
from repositories.config_repo import get_all as config_get_all
from repositories.user_repo import (
    get_by_telegram_id,
    list_users,
    count_users,
    search_users,
    set_active,
    update_role,
    update_limits,
    reset_limits,
)
from repositories.usage_repo import get_requests_count, get_provider_breakdown, get_top_users
from middleware.rate_limit import is_rate_limited, get_retry_after
from services.config_registry import get_config_registry
from services.user_service import ban, unban, set_role as service_set_role
from services.usage_service import get_daily_report, get_user_report

logger = logging.getLogger("blabber")

# Uptime tracking
_BOT_START_TIME = time.time()

# Pending state: chat_id -> {action, key, telegram_id, ...}
_pending: dict[int, dict[str, Any]] = {}

PAGE_SIZE = 10
ROLES = ["user", "moderator", "admin"]
CONFIG_CATEGORIES = ["models", "limits", "tts", "system", "messages"]


def _main_menu_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"))
    kb.add(types.InlineKeyboardButton("⚙️ Конфигурация", callback_data="admin_config"))
    kb.add(types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    kb.add(types.InlineKeyboardButton("🔧 Система", callback_data="admin_system"))
    return kb


def register_admin_handlers(bot: telebot.TeleBot) -> None:
    """Register all admin handlers."""

    @bot.message_handler(commands=["admin"])
    @require_role(bot, min_weight=100)
    def cmd_admin(message: types.Message) -> None:
        bot.reply_to(message, "🔐 Админ-панель", reply_markup=_main_menu_keyboard())

    @bot.message_handler(commands=["ban"])
    @require_role(bot, min_weight=50)
    def cmd_ban(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Использование: /ban <telegram_id>")
            return
        try:
            tid = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Некорректный telegram_id")
            return
        user = get_by_telegram_id(tid)
        if not user:
            bot.reply_to(message, f"❌ Пользователь {tid} не найден")
            return
        if ban(tid):
            bot.reply_to(message, f"✅ Пользователь {tid} заблокирован")
        else:
            bot.reply_to(message, "❌ Ошибка при блокировке")

    @bot.message_handler(commands=["unban"])
    @require_role(bot, min_weight=50)
    def cmd_unban(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Использование: /unban <telegram_id>")
            return
        try:
            tid = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Некорректный telegram_id")
            return
        if unban(tid):
            bot.reply_to(message, f"✅ Пользователь {tid} разблокирован")
        else:
            bot.reply_to(message, f"❌ Пользователь {tid} не найден или ошибка")

    @bot.message_handler(commands=["setrole"])
    @require_role(bot, min_weight=100)
    def cmd_setrole(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Использование: /setrole <telegram_id> <user|moderator|admin>")
            return
        try:
            tid = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Некорректный telegram_id")
            return
        role = parts[2].lower()
        if role not in ROLES:
            bot.reply_to(message, f"❌ Роль должна быть: {', '.join(ROLES)}")
            return
        if service_set_role(tid, role):
            bot.reply_to(message, f"✅ Роль пользователя {tid} изменена на {role}")
        else:
            bot.reply_to(message, f"❌ Пользователь {tid} не найден или ошибка")

    @bot.message_handler(commands=["setconfig"])
    @require_role(bot, min_weight=100)
    def cmd_setconfig(message: types.Message) -> None:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 2:
            bot.reply_to(
                message,
                "❌ Использование: /setconfig <key> <value>\n"
                "Для пустого значения (напр. сброс welcome_message к шаблону из кода): "
                "<code>/setconfig welcome_message</code> без текста после ключа",
                parse_mode="HTML",
            )
            return
        key = parts[1]
        value = parts[2] if len(parts) >= 3 else ""
        reg = get_config_registry()
        row = config_get_all()
        keys = {r["key"] for r in row}
        if key not in keys:
            bot.reply_to(message, f"❌ Ключ '{key}' не найден. Доступные: {', '.join(sorted(keys))}")
            return
        raw = next((r for r in row if r["key"] == key), None)
        if raw:
            reg.set(key, value, raw.get("value_type", "str"), raw.get("category", "general"), updated_by=message.from_user.id)
        bot.reply_to(message, f"✅ {key} = {value}")

    @bot.message_handler(commands=["setlimit", "setlimits"])
    @require_role(bot, min_weight=100)
    def cmd_setlimit(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "❌ Использование: /setlimit <telegram_id> tokens|requests <N>")
            return
        try:
            tid = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Некорректный telegram_id")
            return
        kind = parts[2].lower()
        try:
            n = int(parts[3])
        except ValueError:
            bot.reply_to(message, "❌ N должно быть числом")
            return
        if kind == "tokens":
            ok = update_limits(tid, daily_token_limit=n)
        elif kind == "requests":
            ok = update_limits(tid, daily_request_limit=n)
        else:
            bot.reply_to(message, "❌ Укажи tokens или requests")
            return
        if ok:
            bot.reply_to(message, f"✅ Лимит {kind} для {tid} установлен: {n}")
        else:
            bot.reply_to(message, f"❌ Пользователь {tid} не найден")

    @bot.message_handler(commands=["usage"])
    @require_role(bot, min_weight=100)
    def cmd_usage(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2:
            report = get_daily_report()
            blines = [f"  {p['provider']}: {p['cnt']}" for p in report.get("by_provider", [])]
            blines = blines or ["  (нет данных)"]
            text = (
                "📊 Статистика за сегодня\n\n"
                f"Запросов: {report.get('requests', 0)}\n"
                f"Токенов: {report.get('tokens', 0)}\n"
                f"Стоимость: ${report.get('cost', 0):.4f}\n\n"
                "По провайдерам:\n" + "\n".join(blines)
            )
            bot.reply_to(message, text)
            return
        try:
            tid = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Некорректный telegram_id")
            return
        report = get_user_report(tid, days=7)
        if "error" in report:
            bot.reply_to(message, f"❌ Пользователь {tid} не найден")
            return
        text = (
            f"📊 Пользователь {tid}\n"
            f"@{report.get('username') or '-'}\n\n"
            f"За 7 дней:\n"
            f"  Запросов: {report.get('requests', 0)}\n"
            f"  Токенов: {report.get('tokens', 0)}\n"
            f"  Стоимость: ${report.get('cost', 0):.4f}"
        )
        bot.reply_to(message, text)

    @bot.message_handler(commands=["resetlimits"])
    @require_role(bot, min_weight=100)
    def cmd_resetlimits(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Использование: /resetlimits <telegram_id>")
            return
        try:
            tid = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Некорректный telegram_id")
            return
        if reset_limits(tid):
            bot.reply_to(message, f"✅ Счётчики лимитов для {tid} сброшены")
        else:
            bot.reply_to(message, f"❌ Пользователь {tid} не найден")

    # Handle pending edits (config value, search query)
    def handle_pending_message(message: types.Message) -> bool:
        chat_id = message.chat.id
        if chat_id not in _pending:
            return False
        data = _pending.pop(chat_id)
        action = data.get("action")
        if action == "config_edit":
            key = data.get("key")
            value = message.text.strip()
            reg = get_config_registry()
            raw = next((r for r in config_get_all() if r["key"] == key), None)
            if raw:
                reg.set(key, value, raw.get("value_type", "str"), raw.get("category", "general"), updated_by=message.from_user.id)
            bot.reply_to(message, f"✅ {key} = {value}")
        elif action == "search":
            query = message.text.strip()
            users = search_users(query, limit=15)
            if not users:
                bot.reply_to(message, f"По запросу '{query}' ничего не найдено")
                return True
            lines = []
            for u in users:
                un = u.get("username") or "-"
                fn = u.get("first_name") or ""
                role = u.get("role_name", "")
                status = "✅" if u.get("is_active") else "🚫"
                lines.append(f"{status} {u['telegram_id']} @{un} {fn} ({role})")
            bot.reply_to(message, "Результаты поиска:\n" + "\n".join(lines[:15]))
        return True

    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("admin_"))
    @require_role_callback(bot, min_weight=100)
    def on_admin_callback(call: types.CallbackQuery) -> None:
        if is_rate_limited(call.from_user.id):
            retry = get_retry_after(call.from_user.id)
            bot.answer_callback_query(
                call.id,
                f"⏳ Слишком много команд. Повторите через {retry} сек.",
                show_alert=True,
            )
            return

        data = call.data
        if data == "admin_menu":
            bot.edit_message_text("🔐 Админ-панель", call.message.chat.id, call.message.message_id, reply_markup=_main_menu_keyboard())
            bot.answer_callback_query(call.id)
            return

        if data == "admin_users":
            _show_users_list(bot, call, 0)
            return
        if data.startswith("admin_users_page_"):
            try:
                page = int(data.split("_")[-1])
            except ValueError:
                page = 0
            _show_users_list(bot, call, page)
            return
        if data.startswith("admin_user_role_set_"):
            parts = data[len("admin_user_role_set_"):].rsplit("_", 1)
            if len(parts) == 2:
                tid_s, role = parts
                try:
                    tid_int = int(tid_s)
                    if role in ROLES and service_set_role(tid_int, role):
                        bot.answer_callback_query(call.id, f"Роль: {role}")
                        user = get_by_telegram_id(tid_int)
                        if user:
                            _show_user_card(bot, call, user)
                    else:
                        bot.answer_callback_query(call.id, "Не удалось установить роль")
                except ValueError:
                    bot.answer_callback_query(call.id, "Ошибка")
            else:
                bot.answer_callback_query(call.id)
            return
        if data.startswith("admin_user_"):
            rest = data[len("admin_user_"):]
            if "_" in rest:
                action, tid = rest.split("_", 1)
                try:
                    tid_int = int(tid)
                except ValueError:
                    bot.answer_callback_query(call.id, "Ошибка")
                    return
                if action == "ban":
                    ban(tid_int)
                    bot.answer_callback_query(call.id, "Заблокировано")
                elif action == "unban":
                    unban(tid_int)
                    bot.answer_callback_query(call.id, "Разблокировано")
                elif action == "role":
                    _show_role_picker(bot, call, tid_int)
                    bot.answer_callback_query(call.id)
                    return
                elif action == "reset":
                    if reset_limits(tid_int):
                        bot.answer_callback_query(call.id, "Счётчики сброшены")
                    user = get_by_telegram_id(tid_int)
                    if user:
                        _show_user_card(bot, call, user)
                    else:
                        bot.answer_callback_query(call.id)
                    return
                user = get_by_telegram_id(tid_int)
                if user:
                    _show_user_card(bot, call, user)
            else:
                try:
                    tid_int = int(rest)
                except ValueError:
                    bot.answer_callback_query(call.id, "Ошибка")
                    return
                user = get_by_telegram_id(tid_int)
                if user:
                    _show_user_card(bot, call, user)
            bot.answer_callback_query(call.id)
            return

        if data == "admin_config":
            _show_config_categories(bot, call)
            return
        if data.startswith("admin_config_cat_"):
            cat = data[len("admin_config_cat_"):]
            _show_config_list(bot, call, cat)
            return
        if data.startswith("admin_config_edit_"):
            key = data[len("admin_config_edit_"):]
            _pending[call.message.chat.id] = {"action": "config_edit", "key": key}
            bot.edit_message_text(
                f"Введите новое значение для {key} (отправьте сообщением):",
                call.message.chat.id, call.message.message_id
            )
            bot.answer_callback_query(call.id)
            return

        if data == "admin_stats":
            _show_stats(bot, call)
            return

        if data == "admin_system":
            _show_system(bot, call)
            return
        if data == "admin_system_maintenance":
            reg = get_config_registry()
            cur = reg.get("maintenance_mode") or False
            reg.set("maintenance_mode", not cur, "bool", "system", updated_by=call.from_user.id)
            status = "включён" if (not cur) else "выключен"
            bot.answer_callback_query(call.id, f"Maintenance mode {status}")
            _show_system(bot, call)
            return

        if data == "admin_users_search":
            _pending[call.message.chat.id] = {"action": "search"}
            bot.edit_message_text(
                "Введите username или telegram_id для поиска:",
                call.message.chat.id, call.message.message_id
            )
            bot.answer_callback_query(call.id)
            return

        bot.answer_callback_query(call.id)

    # Handler for pending admin actions (config edit, search)
    @bot.message_handler(func=lambda m: m.text and not m.text.startswith("/") and m.chat.id in _pending)
    @require_role(bot, min_weight=100)
    def handle_pending_msg(message: types.Message) -> None:
        handle_pending_message(message)


def _show_users_list(bot: telebot.TeleBot, call: types.CallbackQuery, page: int) -> None:
    try:
        total = count_users()
        users = list_users(offset=page * PAGE_SIZE, limit=PAGE_SIZE)
    except Exception as e:
        logger.exception("admin_users_list_failed", extra={"event": "admin_users_list_failed", "error": str(e)})
        bot.answer_callback_query(call.id, "Ошибка загрузки списка", show_alert=True)
        return
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    lines = []
    for u in users:
        un = u.get("username") or "-"
        fn = u.get("first_name") or ""
        role = u.get("role_name", "")
        status = "✅" if u.get("is_active") else "🚫"
        lines.append(f"{status} {u['telegram_id']} @{un} {fn} ({role})")
    text = f"👥 Пользователи (стр. {page + 1}/{total_pages}, всего {total})\n\n" + "\n".join(lines)
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for u in users:
        btns.append(types.InlineKeyboardButton(
            f"👤 {u.get('telegram_id')}",
            callback_data=f"admin_user_{u['telegram_id']}"
        ))
    for i in range(0, len(btns), 2):
        row = btns[i:i + 2]
        kb.row(*row)
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("◀ Назад", callback_data=f"admin_users_page_{page - 1}"))
    if page < total_pages - 1:
        nav.append(types.InlineKeyboardButton("Вперёд ▶", callback_data=f"admin_users_page_{page + 1}"))
    if nav:
        kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔍 Поиск", callback_data="admin_users_search"))
    kb.add(types.InlineKeyboardButton("⬅ Меню", callback_data="admin_menu"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception as e:
        logger.warning("admin_edit_failed", extra={"event": "admin_edit_failed", "error": str(e)})
    bot.answer_callback_query(call.id)


def _show_user_card(bot: telebot.TeleBot, call: types.CallbackQuery, user: dict) -> None:
    tid = user["telegram_id"]
    status = "✅ Активен" if user.get("is_active") else "🚫 Заблокирован"
    text = (
        f"👤 Пользователь {tid}\n"
        f"Username: @{user.get('username') or '-'}\n"
        f"Имя: {user.get('first_name') or '-'}\n"
        f"Роль: {user.get('role_name')}\n"
        f"Статус: {status}\n"
        f"Лимиты: {user.get('tokens_used_today', 0)}/{user.get('daily_token_limit')} токенов, "
        f"{user.get('requests_today', 0)}/{user.get('daily_request_limit')} запросов\n"
        f"Модель: {user.get('preferred_model')}\n"
        f"Регистрация: {user.get('created_at', '')}"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    if user.get("is_active"):
        kb.add(types.InlineKeyboardButton("🚫 Заблокировать", callback_data=f"admin_user_ban_{tid}"))
    else:
        kb.add(types.InlineKeyboardButton("✅ Разблокировать", callback_data=f"admin_user_unban_{tid}"))
    kb.add(types.InlineKeyboardButton("🔄 Роль", callback_data=f"admin_user_role_{tid}"))
    kb.add(types.InlineKeyboardButton("🔄 Сбросить счётчики", callback_data=f"admin_user_reset_{tid}"))
    kb.add(types.InlineKeyboardButton("⬅ К списку", callback_data="admin_users"))
    kb.add(types.InlineKeyboardButton("⬅ Меню", callback_data="admin_menu"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception as e:
        logger.warning("admin_user_card_edit_failed", extra={"event": "admin_user_card_edit_failed", "tid": tid, "error": str(e)})


def _show_role_picker(bot: telebot.TeleBot, call: types.CallbackQuery, tid: int) -> None:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for r in ROLES:
        kb.add(types.InlineKeyboardButton(r.capitalize(), callback_data=f"admin_user_role_set_{tid}_{r}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data=f"admin_user_{tid}"))
    try:
        bot.edit_message_text("Выберите роль:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        pass


def _show_config_categories(bot: telebot.TeleBot, call: types.CallbackQuery) -> None:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for cat in CONFIG_CATEGORIES:
        kb.add(types.InlineKeyboardButton(cat, callback_data=f"admin_config_cat_{cat}"))
    kb.add(types.InlineKeyboardButton("⬅ Меню", callback_data="admin_menu"))
    try:
        bot.edit_message_text("⚙️ Конфигурация — выберите категорию:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        pass
    bot.answer_callback_query(call.id)


def _show_config_list(bot: telebot.TeleBot, call: types.CallbackQuery, category: str) -> None:
    rows = config_get_all(category)
    if not rows:
        text = f"Параметров в категории {category} нет."
    else:
        lines = []
        kb = types.InlineKeyboardMarkup(row_width=1)
        for r in rows:
            val = r["value"]
            if r.get("is_secret"):
                val = "***"
            lines.append(f"{r['key']}: {val}")
            kb.add(types.InlineKeyboardButton(f"✏️ {r['key']}", callback_data=f"admin_config_edit_{r['key']}"))
        text = f"⚙️ {category}\n\n" + "\n".join(lines)
        kb.add(types.InlineKeyboardButton("⬅ Категории", callback_data="admin_config"))
        kb.add(types.InlineKeyboardButton("⬅ Меню", callback_data="admin_menu"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception as e:
        logger.warning("admin_config_list_edit_failed", extra={"event": "admin_config_list_edit_failed", "category": category, "error": str(e)})
    bot.answer_callback_query(call.id)


def _show_stats(bot: telebot.TeleBot, call: types.CallbackQuery) -> None:
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    today_start = (now.replace(hour=0, minute=0, second=0, microsecond=0)).strftime("%Y-%m-%d %H:%M:%S")
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    total_users = count_users()
    active_users = sum(1 for _ in [1] if True)  # is_active count
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM users WHERE is_active = 1").fetchone()
        active_users = row["cnt"] if row else 0

    req_today = get_requests_count(today_start, now_str)
    req_week = get_requests_count(week_start, now_str)
    breakdown = get_provider_breakdown(week_start, now_str)
    top = get_top_users(5, week_start, now_str)

    blines = [f"  {b['provider']}: {b['cnt']}" for b in breakdown] if breakdown else ["  (нет данных)"]
    tlines = []
    for t in top:
        un = t.get("username") or "-"
        tlines.append(f"  {t['telegram_id']} @{un} — {t['req_count']} запр.")
    if not tlines:
        tlines = ["  (нет данных)"]

    text = (
        "📊 Статистика\n\n"
        f"Пользователей: {total_users} (активных: {active_users})\n"
        f"Запросов сегодня: {req_today}\n"
        f"Запросов за неделю: {req_week}\n\n"
        "По провайдерам (неделя):\n" + "\n".join(blines) + "\n\n"
        "Топ-5 пользователей (неделя):\n" + "\n".join(tlines)
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅ Меню", callback_data="admin_menu"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception as e:
        logger.warning("admin_stats_edit_failed", extra={"event": "admin_stats_edit_failed", "error": str(e)})
    bot.answer_callback_query(call.id)


def _show_system(bot: telebot.TeleBot, call: types.CallbackQuery) -> None:
    reg = get_config_registry()
    maintenance = reg.get("maintenance_mode") or False
    uptime_sec = int(time.time() - _BOT_START_TIME)
    uptime_str = f"{uptime_sec // 3600}ч {(uptime_sec % 3600) // 60}м"
    db_path = get_db_path()
    db_size = os.path.getsize(db_path) / 1024 if db_path.exists() else 0
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    text = (
        "🔧 Система\n\n"
        f"Python: {py_ver}\n"
        f"Uptime: {uptime_str}\n"
        f"БД: {db_size:.1f} KB\n"
        f"Maintenance mode: {'✅ Включён' if maintenance else '❌ Выключен'}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "🔄 " + ("Выключить" if maintenance else "Включить") + " maintenance",
        callback_data="admin_system_maintenance"
    ))
    kb.add(types.InlineKeyboardButton("⬅ Меню", callback_data="admin_menu"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception as e:
        logger.warning("admin_system_edit_failed", extra={"event": "admin_system_edit_failed", "error": str(e)})
    bot.answer_callback_query(call.id)


def check_pending_message(chat_id: int) -> bool:
    """Return True if chat has pending admin action (to intercept message)."""
    return chat_id in _pending
