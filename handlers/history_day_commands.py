"""
Команды сценария `История дня`.

Основные точки входа:
  /historyday
  /history

Подкоманды:
  /historyday fact [date]
  /historyday image [date|question]
  /historyday context [question]
  /historyday memory
  /historyday clear
"""

from __future__ import annotations

import telebot
from telebot import types

from middleware.auth import with_user_check
from services import history_day_fact_service as fact_svc
from services.history_day_orchestrator import (
    clear_history_day_memory,
    get_history_day_status,
    get_history_day_memory_snapshot,
    get_latest_history_day_event_date,
    run_fact_scenario,
    run_image_scenario,
    run_saved_context_scenario,
)


def _send_long_message(bot: telebot.TeleBot, chat_id: int, text: str, **kwargs) -> None:
    limit = 4000
    if len(text or "") <= limit:
        bot.send_message(chat_id, text, **kwargs)
        return
    remaining = text or ""
    while remaining:
        chunk = remaining[:limit]
        cut = max(chunk.rfind("\n\n"), chunk.rfind("\n"), chunk.rfind(" "))
        if cut <= 0 or len(remaining) <= limit:
            cut = min(len(remaining), limit)
        bot.send_message(chat_id, remaining[:cut], **kwargs)
        remaining = remaining[cut:].lstrip()


def _status_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📅 Факт дня", callback_data="historyday_fact_today"),
        types.InlineKeyboardButton("🖼 Изображение и анализ", callback_data="historyday_image_today"),
    )
    kb.add(
        types.InlineKeyboardButton("🧠 О чем ты рассказывал?", callback_data="historyday_ctx_summary"),
        types.InlineKeyboardButton("📆 С каким годом связано?", callback_data="historyday_ctx_year"),
    )
    kb.add(
        types.InlineKeyboardButton("👤 Напомни событие", callback_data="historyday_ctx_event"),
        types.InlineKeyboardButton("🧹 Очистить память", callback_data="historyday_clear"),
    )
    return kb


def _followup_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🖼 Показать изображение", callback_data="historyday_image_today"),
        types.InlineKeyboardButton("🧠 Что ты только что рассказывал?", callback_data="historyday_ctx_summary"),
    )
    kb.add(
        types.InlineKeyboardButton("📆 С каким годом связано?", callback_data="historyday_ctx_year"),
        types.InlineKeyboardButton("🧹 Очистить память", callback_data="historyday_clear"),
    )
    return kb


def _resolve_image_request(tail: str, latest_event_date: str) -> dict[str, str]:
    """
    Resolve `/historyday image ...` into either:
    - explicit date request
    - follow-up image question using latest saved event_date
    - empty/default request
    """
    tail = (tail or "").strip()
    if not tail:
        return {"mode": "default", "date": "", "image_question": "", "error": ""}

    normalized_tail = fact_svc.normalize_requested_date(tail)
    if normalized_tail.get("ok"):
        return {"mode": "date", "date": tail, "image_question": "", "error": ""}

    if latest_event_date:
        return {
            "mode": "question",
            "date": latest_event_date,
            "image_question": tail,
            "error": "",
        }

    return {
        "mode": "question_missing_context",
        "date": "",
        "image_question": tail,
        "error": (
            "🖼 Сначала нужно получить факт дня или изображение, чтобы у меня появился "
            "контекст для follow-up вопроса про картинку.\n\n"
            "Попробуй сначала:\n"
            "<code>/historyday fact</code>\n"
            "или\n"
            "<code>/historyday image</code>"
        ),
    }


def _format_scenario_tag(tag: str) -> str:
    mapping = {
        "history_day_fact": "Факт дня",
        "history_day_image": "Изображение и анализ",
        "history_day_context": "Вопрос по памяти",
    }
    return mapping.get((tag or "").strip(), tag or "Неизвестный шаг")


def _build_status_text(user_id: int) -> str:
    status = get_history_day_status(user_id)
    memory_state = "доступна" if status["memory_available"] else "ограничена: не настроены embeddings"
    vision_state = "доступен" if status["vision_available"] else "недоступен: будет честное описание по метаданным"
    return (
        "🏛 <b>История дня</b>\n\n"
        "Отдельный сценарий бота с тремя режимами:\n"
        "1. <b>Факт дня</b>\n"
        "2. <b>Изображение и анализ</b>\n"
        "3. <b>Ответ по сохраненному контексту из LanceDB</b>\n\n"
        f"🧠 Сохраненных сообщений сценария: <b>{status['saved_messages_count']}</b>\n"
        f"🔎 Память LanceDB: <b>{memory_state}</b>\n"
        f"👁 Vision-анализ: <b>{vision_state}</b>\n\n"
        "<b>Команды</b>\n"
        "<code>/historyday</code> или <code>/history</code> — эта карточка\n"
        "<code>/historyday help</code> / <code>/historyday status</code> — повторно показать карточку сценария\n"
        "<code>/historyday fact</code> [MM-DD | YYYY-MM-DD] — факт дня\n"
        "<code>/historyday image</code> [дата или вопрос] — изображение и анализ\n"
        "<code>/historyday context &lt;вопрос&gt;</code> — ответ по сохраненной памяти\n"
        "<code>/historyday memory</code> — диагностика памяти сценария\n"
        "<code>/historyday clear</code> — очистить память сценария\n\n"
        "<i>Можно пользоваться кнопками ниже для быстрого сценария.</i>"
    )


def _build_memory_snapshot_text(user_id: int) -> str:
    snapshot = get_history_day_memory_snapshot(user_id, limit=8)
    memory_state = "доступна" if snapshot["memory_available"] else "недоступна: не настроены embeddings"
    lines = [
        "🧠 <b>Память сценария `История дня`</b>",
        "",
        f"Всего сохраненных записей: <b>{snapshot['saved_messages_count']}</b>",
        f"Семантическая память: <b>{memory_state}</b>",
        f"Последняя дата события: <b>{snapshot['latest_event_date'] or 'не найдена'}</b>",
    ]
    items = snapshot.get("items") or []
    if not items:
        lines.extend(["", "Пока сохраненных записей нет."])
        return "\n".join(lines)

    lines.extend(["", "<b>Последние записи</b>"])
    for idx, item in enumerate(items, start=1):
        lines.append(
            f"{idx}. <b>{_format_scenario_tag(item['scenario_tag'])}</b> · "
            f"{item['event_date'] or '-'} · "
            f"{item['created_at'] or '-'}"
        )
        lines.append(f"   {item['text']}")
    return "\n".join(lines)


def _send_image_result(bot: telebot.TeleBot, chat_id: int, payload: dict) -> None:
    image_url = (payload.get("image_url") or "").strip()
    caption = payload.get("photo_caption") or "История дня"
    text = payload.get("text") or ""
    reply_markup = _followup_keyboard()
    if image_url:
        try:
            bot.send_photo(chat_id, image_url, caption=caption, reply_markup=reply_markup)
        except Exception:
            bot.send_message(
                chat_id,
                f"🖼 Изображение: {image_url}",
                reply_markup=reply_markup,
                disable_web_page_preview=False,
            )
    _send_long_message(
        bot,
        chat_id,
        text,
        parse_mode="HTML",
        disable_web_page_preview=False,
    )


def _run_fact(bot: telebot.TeleBot, chat_id: int, user_id: int, user_message: str, date: str = "") -> None:
    wait = bot.send_message(chat_id, "⏳ Собираю исторический факт дня...")
    payload = run_fact_scenario(user_id, user_message=user_message, date=date)
    try:
        bot.delete_message(chat_id, wait.message_id)
    except Exception:
        pass
    _send_long_message(
        bot,
        chat_id,
        payload["text"],
        parse_mode="HTML",
        disable_web_page_preview=False,
        reply_markup=_followup_keyboard() if payload.get("ok") else _status_keyboard(),
    )


def _run_image(
    bot: telebot.TeleBot,
    chat_id: int,
    user_id: int,
    user_message: str,
    date: str = "",
    image_question: str = "",
) -> None:
    wait = bot.send_message(chat_id, "⏳ Ищу изображение по факту дня и готовлю анализ...")
    payload = run_image_scenario(
        user_id,
        user_message=user_message,
        date=date,
        image_question=image_question,
    )
    try:
        bot.delete_message(chat_id, wait.message_id)
    except Exception:
        pass
    if payload.get("ok"):
        _send_image_result(bot, chat_id, payload)
        return
    _send_long_message(
        bot,
        chat_id,
        payload["text"],
        parse_mode="HTML",
        reply_markup=_status_keyboard(),
    )


def _run_context(bot: telebot.TeleBot, chat_id: int, user_id: int, user_message: str) -> None:
    wait = bot.send_message(chat_id, "⏳ Поднимаю сохраненный контекст из LanceDB...")
    payload = run_saved_context_scenario(user_id, user_message=user_message)
    try:
        bot.delete_message(chat_id, wait.message_id)
    except Exception:
        pass
    _send_long_message(
        bot,
        chat_id,
        payload["text"],
        parse_mode="HTML",
        reply_markup=_followup_keyboard(),
    )


def register_history_day_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["historyday", "history"])
    @with_user_check(bot)
    def handle_history_day(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        parts = (message.text or "").split(maxsplit=2)

        if len(parts) < 2:
            bot.send_message(
                chat_id,
                _build_status_text(user_id),
                parse_mode="HTML",
                reply_markup=_status_keyboard(),
            )
            return

        command = (parts[1] or "").strip().lower()
        tail = parts[2].strip() if len(parts) >= 3 else ""

        if command in {"help", "status"}:
            bot.send_message(
                chat_id,
                _build_status_text(user_id),
                parse_mode="HTML",
                reply_markup=_status_keyboard(),
            )
            return

        if command == "fact":
            _run_fact(
                bot,
                chat_id,
                user_id,
                user_message=message.text,
                date=tail,
            )
            return

        if command == "image":
            resolved = _resolve_image_request(tail, get_latest_history_day_event_date(user_id))
            if resolved["error"]:
                bot.send_message(
                    chat_id,
                    resolved["error"],
                    parse_mode="HTML",
                    reply_markup=_status_keyboard(),
                )
                return

            _run_image(
                bot,
                chat_id,
                user_id,
                user_message=message.text,
                date=resolved["date"],
                image_question=resolved["image_question"],
            )
            return

        if command == "context":
            question = tail or "О чем ты мне только что рассказывал?"
            _run_context(bot, chat_id, user_id, user_message=question)
            return

        if command == "memory":
            bot.send_message(
                chat_id,
                _build_memory_snapshot_text(user_id),
                parse_mode="HTML",
                reply_markup=_status_keyboard(),
            )
            return

        if command == "clear":
            payload = clear_history_day_memory(user_id)
            bot.send_message(
                chat_id,
                payload["text"],
                reply_markup=_status_keyboard(),
            )
            return

        bot.send_message(
            chat_id,
            _build_status_text(user_id),
            parse_mode="HTML",
            reply_markup=_status_keyboard(),
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("historyday_"))
    def callback_history_day(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        data = call.data

        if data == "historyday_fact_today":
            bot.answer_callback_query(call.id, "Собираю факт дня…")
            _run_fact(bot, chat_id, user_id, user_message="Что произошло сегодня в истории?", date="")
            return

        if data == "historyday_image_today":
            bot.answer_callback_query(call.id, "Ищу изображение…")
            _run_image(bot, chat_id, user_id, user_message="Покажи изображение по факту дня и объясни его", date="")
            return

        if data == "historyday_ctx_summary":
            bot.answer_callback_query(call.id, "Поднимаю сохраненный контекст…")
            _run_context(bot, chat_id, user_id, user_message="О чем ты мне только что рассказывал?")
            return

        if data == "historyday_ctx_year":
            bot.answer_callback_query(call.id, "Смотрю, с каким годом это связано…")
            _run_context(bot, chat_id, user_id, user_message="С каким годом это связано?")
            return

        if data == "historyday_ctx_event":
            bot.answer_callback_query(call.id, "Поднимаю событие из памяти…")
            _run_context(bot, chat_id, user_id, user_message="Напомни ключевую фигуру или событие")
            return

        if data == "historyday_clear":
            payload = clear_history_day_memory(user_id)
            bot.answer_callback_query(call.id, "Память сценария очищена" if payload["ok"] else "Не получилось очистить память")
            bot.send_message(chat_id, payload["text"], reply_markup=_status_keyboard())
            return
