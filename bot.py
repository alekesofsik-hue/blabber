"""
Telegram-бот Blabber — балабол, который любит трепаться и болтать.
"""

import logging
import os
import time
import uuid

import requests
import telebot
from dotenv import load_dotenv
from telebot import types

import services.cbr_service as cbr_svc
import services.context_service as ctx_svc
import services.knowledge_service as kb_svc
import services.persona_service as persona_svc
import services.profile_service as profile_svc
import services.auto_memory_service as am_svc
from database import init_db
from middleware.auth import with_user_check
from bot_texts import resolve_help_message, resolve_start_message
from services.config_registry import get_config_registry, get_setting
from telemetry import setup_telemetry, text_meta, user_id_hash
from tts import get_available_voices, synthesize_voice
from user_storage import (
    get_available_models,
    get_user_model,
    get_user_voice,
    is_agent_enabled,
    is_kb_enabled,
    is_voice_enabled,
    set_user_model,
    set_user_voice,
    set_voice_enabled,
)
from utils import DEFAULT_SYSTEM_MESSAGE, get_chat_response

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен в переменных окружения")

# Создаем экземпляр бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

logger = setup_telemetry("blabber")

# Инициализация базы данных (создание таблиц, применение миграций)
_DB_AVAILABLE = True
try:
    init_db()
except Exception as _db_err:
    _DB_AVAILABLE = False
    logging.getLogger("blabber").error(
        "db_init_failed",
        extra={
            "event": "db_init_failed",
            "error": str(_db_err),
            "fallback": "bot will run with .env defaults only",
        },
    )

# Загрузка динамической конфигурации из БД (перезаписывает .env)
if _DB_AVAILABLE:
    try:
        get_config_registry().load()
    except Exception as _cfg_err:
        logging.getLogger("blabber").warning(
            "config_load_failed",
            extra={
                "event": "config_load_failed",
                "error": str(_cfg_err),
                "fallback": "falling back to .env / hardcoded defaults",
            },
        )

# Регистрация хендлеров (до остальных, чтобы pending перехватывал сообщения)
from handlers import (  # noqa: E402
    register_admin_handlers,
    register_agent_handlers,
    register_knowledge_handlers,
    register_persona_handlers,
    register_profile_handlers,
    register_quote_handlers,
    register_report_handlers,
)

register_admin_handlers(bot)
register_profile_handlers(bot)
register_knowledge_handlers(bot)
register_persona_handlers(bot)
register_agent_handlers(bot)
register_quote_handlers(bot)
register_report_handlers(bot)

# Лимит Telegram на длину одного сообщения
TG_MSG_LIMIT = 4096


def _build_system_message(
    has_profile: bool,
    has_kb_context: bool,
    persona_prompt: str | None = None,
    convo_summary: str | None = None,
) -> str:
    """
    Build the adaptive system message for the current request.

    Base persona: balabool — chatty, witty, friendly.
    Extra guardrails activate only when external memory is injected,
    so the fun personality is preserved for ordinary conversation.
    If a role persona is set, its system_prompt is appended as a focus layer.
    """
    msg = DEFAULT_SYSTEM_MESSAGE

    if persona_prompt:
        msg += f"\n\nРоль для этого разговора: {persona_prompt}"

    if convo_summary:
        msg += (
            "\n\nКраткое резюме предыдущей беседы (для связности ответов):\n"
            f"{convo_summary}"
        )

    if has_profile:
        msg += (
            "\n\nВажно: тебе переданы личные факты о собеседнике. "
            "Учитывай их в ответе естественно — не зачитывай список вслух "
            "и не говори «я помню о тебе то-то». Просто используй как контекст."
        )

    if has_kb_context:
        msg += (
            "\n\nВажно: в этом запросе тебе переданы факты из базы знаний собеседника "
            "(раздел «[Факты из базы знаний]»). "
            "Используй их точно — не выдумывай то, чего там нет. "
            "Если ответа в базе нет — честно скажи, что не нашёл. "
            "Шутить и болтать можно, главное — факты не искажай."
        )

    return msg


def _memory_suggestion_text(items: list[dict]) -> str:
    lines: list[str] = ["🧠 <b>Предложение памяти</b>\n", "Хочешь, я запомню это про тебя?\n"]
    for i, it in enumerate(items, start=1):
        kind = it.get("kind") or "fact"
        label = "Предпочтение" if kind == "preference" else "Факт"
        status = it.get("status") or "pending"
        mark = "✅ " if status == "saved" else ""
        text = it.get("text") or ""
        evidence = (it.get("evidence") or "").strip()
        lines.append(f"{mark}<b>{i}. {label}:</b> {text}")
        if evidence:
            lines.append(f"<i>цитата: “{evidence}”</i>")
        lines.append("")
    lines.append("Можно пропустить или отключить такие подсказки.")
    return "\n".join(lines).strip()


def _memory_keyboard(suggestion_id: str, items: list[dict]) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    for idx, it in enumerate(items):
        status = it.get("status") or "pending"
        if status == "saved":
            kb.add(types.InlineKeyboardButton(f"✅ #{idx+1} сохранено", callback_data="mem_na"))
        else:
            kb.add(types.InlineKeyboardButton(f"✅ Запомнить #{idx+1}", callback_data=f"mem_a_{suggestion_id}_{idx}"))
    kb.add(types.InlineKeyboardButton("✅ Запомнить всё", callback_data=f"mem_all_{suggestion_id}"))
    kb.add(
        types.InlineKeyboardButton("⏭ Не сейчас", callback_data=f"mem_skip_{suggestion_id}"),
        types.InlineKeyboardButton("🚫 Не предлагать", callback_data=f"mem_off_{suggestion_id}"),
    )
    return kb


def _split_text(text: str, limit: int = TG_MSG_LIMIT) -> list[str]:
    """
    Разбить длинный текст на части, не превышающие limit символов.

    Старается резать по абзацам (\\n\\n), затем по строкам (\\n),
    затем по пробелам, и только в крайнем случае — по жёсткому лимиту.
    """
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        # Ищем лучшее место для разрыва (приоритет: абзац > строка > пробел)
        cut = -1
        for sep in ("\n\n", "\n", " "):
            pos = text.rfind(sep, 0, limit)
            if pos > 0:
                cut = pos + len(sep)
                break

        if cut <= 0:
            # Не нашли разделитель — режем по жёсткому лимиту
            cut = limit

        chunks.append(text[:cut])
        text = text[cut:]

    return chunks


def send_long_message(chat_id: int, text: str, **kwargs) -> None:
    """
    Отправить сообщение в Telegram, при необходимости разбив на части.
    """
    for chunk in _split_text(text):
        bot.send_message(chat_id, chunk, **kwargs)


@bot.message_handler(commands=["start"])
@with_user_check(bot)
def handle_start(message):
    """Обработчик команды /start"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    logger.info(
        "command_start",
        extra={
            "event": "command_start",
            "user_id_hash": user_id_hash(user_id),
        },
    )
    
    model_label = get_available_models().get(get_user_model(user_id), "неизвестна")
    # Текст по умолчанию — bot_texts/defaults.py; переопределение: config welcome_message (пусто = шаблон из кода)
    welcome_text, welcome_mode = resolve_start_message(model_label, get_setting("welcome_message"))
    extra = {"parse_mode": welcome_mode} if welcome_mode else {}
    bot.send_message(chat_id, welcome_text, **extra)


@bot.message_handler(commands=["help"])
@with_user_check(bot)
def handle_help(message):
    """Обработчик команды /help"""
    chat_id = message.chat.id

    logger.info(
        "command_help",
        extra={
            "event": "command_help",
        },
    )
    
    # Шаблон по умолчанию — bot_texts/defaults.py; переопределение: config help_message (пусто = шаблон из кода)
    help_text, help_mode = resolve_help_message(get_setting("help_message"))
    kw: dict = {}
    if help_mode:
        kw["parse_mode"] = help_mode
    send_long_message(chat_id, help_text, **kw)


@bot.message_handler(commands=["models"])
@with_user_check(bot)
def handle_models(message):
    """Обработчик команды /models - показать доступные модели"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    logger.info(
        "command_models",
        extra={
            "event": "command_models",
            "user_id_hash": user_id_hash(user_id),
        },
    )
    
    current_model = get_user_model(user_id)
    available_models = get_available_models()
    
    models_text = "🤖 Доступные модели:\n\n"
    for key, name in available_models.items():
        marker = "✅" if key == current_model else "⚪"
        models_text += f"{marker} {name} ({key})\n"
    
    models_text += f"\nТекущая модель: {available_models.get(current_model, 'неизвестна')}\n"
    models_text += "\nПереключение: /model название из списка выше\n"
    models_text += "Все команды бота: /help"
    
    bot.send_message(chat_id, models_text)


@bot.message_handler(commands=["model"])
@with_user_check(bot)
def handle_model(message):
    """Обработчик команды /model - переключить модель"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Получаем аргументы команды
    parts = message.text.split()
    
    if len(parts) < 2:
        bot.send_message(
            chat_id,
            "❌ Укажи модель!\n\n"
            "Примеры:\n"
            "/model gigachat\n"
            "/model openrouter\n"
            "/model reasoning\n"
            "/model openai\n"
            "/model yandexgpt\n"
            "/model ollama\n\n"
            "Используй /models чтобы увидеть список доступных моделей"
        )
        return
    
    model_name = parts[1].lower()
    available_models = get_available_models()
    
    if model_name not in available_models:
        logger.info(
            "model_switch_invalid",
            extra={
                "event": "model_switch_invalid",
                "user_id_hash": user_id_hash(user_id),
                "requested_model": model_name,
            },
        )
        bot.send_message(
            chat_id,
            f"❌ Модель '{model_name}' не найдена!\n\n"
            f"Доступные модели: {', '.join(available_models.keys())}\n"
            "Используй /models чтобы увидеть список"
        )
        return
    
    # Устанавливаем модель
    prev_model = get_user_model(user_id)
    if set_user_model(user_id, model_name):
        logger.info(
            "model_switched",
            extra={
                "event": "model_switched",
                "user_id_hash": user_id_hash(user_id),
                "prev_model": prev_model,
                "new_model": model_name,
            },
        )
        bot.send_message(
            chat_id,
            f"✅ Модель переключена на: {available_models[model_name]}\n\n"
            "Теперь я буду использовать эту модель для ответов!"
        )
    else:
        logger.warning(
            "model_switch_failed",
            extra={
                "event": "model_switch_failed",
                "user_id_hash": user_id_hash(user_id),
                "requested_model": model_name,
            },
        )
        bot.send_message(chat_id, "❌ Ошибка при переключении модели")


@bot.message_handler(commands=["voice"])
@with_user_check(bot)
def handle_voice(message):
    """
    Обработчик команды /voice — управление голосовыми ответами.

    /voice          — показать текущее состояние
    /voice on       — включить озвучку
    /voice off      — выключить озвучку
    /voice alena    — сменить голос на Алёну (женский)
    /voice filipp   — сменить голос на Филиппа (мужской)
    """
    chat_id = message.chat.id
    user_id = message.from_user.id

    parts = message.text.split()
    available_voices = get_available_voices()

    # Без аргумента — показать статус
    if len(parts) < 2:
        enabled = is_voice_enabled(user_id)
        current_voice = get_user_voice(user_id)
        status = "включена" if enabled else "выключена"

        voice_list = "\n".join(
            f"  {'✅' if k == current_voice else '⚪'} /voice {k} — {desc}"
            for k, desc in available_voices.items()
        )

        bot.send_message(
            chat_id,
            f"🔊 Озвучка: {status}\n"
            f"🎙 Голос: {available_voices.get(current_voice, current_voice)}\n\n"
            f"Управление:\n"
            f"  /voice on — включить озвучку\n"
            f"  /voice off — выключить озвучку\n\n"
            f"Выбор голоса:\n{voice_list}"
        )
        return

    arg = parts[1].lower()

    if arg == "on":
        set_voice_enabled(user_id, True)
        current_voice = get_user_voice(user_id)
        logger.info(
            "voice_enabled",
            extra={
                "event": "voice_enabled",
                "user_id_hash": user_id_hash(user_id),
                "voice": current_voice,
            },
        )
        bot.send_message(
            chat_id,
            f"🔊 Озвучка включена!\n"
            f"🎙 Голос: {available_voices.get(current_voice, current_voice)}\n\n"
            f"Теперь после текстового ответа я буду отправлять голосовое сообщение.\n"
            f"Чтобы сменить голос: /voice alena или /voice filipp"
        )

    elif arg == "off":
        set_voice_enabled(user_id, False)
        logger.info(
            "voice_disabled",
            extra={
                "event": "voice_disabled",
                "user_id_hash": user_id_hash(user_id),
            },
        )
        bot.send_message(chat_id, "🔇 Озвучка выключена.")

    elif arg in available_voices:
        set_user_voice(user_id, arg)
        # Автоматически включаем озвучку при выборе голоса
        set_voice_enabled(user_id, True)
        logger.info(
            "voice_changed",
            extra={
                "event": "voice_changed",
                "user_id_hash": user_id_hash(user_id),
                "voice": arg,
            },
        )
        bot.send_message(
            chat_id,
            f"🎙 Голос изменён на: {available_voices[arg]}\n"
            f"🔊 Озвучка включена."
        )

    else:
        voice_options = ", ".join(available_voices.keys())
        bot.send_message(
            chat_id,
            f"❌ Неизвестный аргумент: '{arg}'\n\n"
            f"Доступные команды:\n"
            f"  /voice on — включить\n"
            f"  /voice off — выключить\n"
            f"  /voice <голос> — сменить голос ({voice_options})"
        )


def _mode_keyboard(current_mode: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    chat_mark = "✅ " if current_mode == "chat" else ""
    single_mark = "✅ " if current_mode == "single" else ""
    kb.add(types.InlineKeyboardButton(
        f"{chat_mark}💬 Чат (с памятью)", callback_data="ctx_mode_chat"
    ))
    kb.add(types.InlineKeyboardButton(
        f"{single_mark}💡 Вопрос-ответ (без памяти)", callback_data="ctx_mode_single"
    ))
    return kb


def _clear_confirm_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Да, очистить", callback_data=f"ctx_clear_yes_{user_id}"),
        types.InlineKeyboardButton("❌ Нет, оставить", callback_data=f"ctx_clear_no_{user_id}"),
    )
    return kb


@bot.message_handler(commands=["mode"])
@with_user_check(bot)
def handle_mode(message):
    """Обработчик команды /mode — переключение режима разговора."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) >= 2:
        arg = parts[1].lower()
        if arg == "chat":
            ctx_svc.set_mode(user_id, "chat")
            bot.send_message(
                chat_id,
                "💬 Режим переключён на <b>Чат (с памятью)</b>.\n"
                "Я буду помнить нашу беседу. Чтобы начать с чистого листа — /reset",
                parse_mode="HTML",
            )
            return
        if arg in ("single", "qa"):
            ctx_svc.set_mode(user_id, "single")
            bot.send_message(chat_id, "💡 Режим переключён на <b>Вопрос-ответ</b>. Каждый запрос — независимый.", parse_mode="HTML")
            return

    current = ctx_svc.get_mode(user_id)
    mode_label = "💬 Чат (с памятью)" if current == "chat" else "💡 Вопрос-ответ (без памяти)"
    msg_count = ctx_svc.get_message_count(user_id) if current == "chat" else 0
    text = (
        f"🔀 <b>Режим разговора</b>\n\n"
        f"Сейчас: {mode_label}\n"
    )
    if current == "chat" and msg_count > 0:
        text += f"Сохранено реплик: {msg_count}\n"
    text += "\nВыбери режим:"
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=_mode_keyboard(current))


@bot.callback_query_handler(func=lambda c: c.data in ("ctx_mode_chat", "ctx_mode_single"))
def callback_mode(call):
    user_id = call.from_user.id
    new_mode = "chat" if call.data == "ctx_mode_chat" else "single"
    ctx_svc.set_mode(user_id, new_mode)

    if new_mode == "chat":
        answer = "💬 Режим: Чат (с памятью). Буду помнить наш разговор!"
        notice = "Чтобы очистить историю: /reset"
    else:
        answer = "💡 Режим: Вопрос-ответ. Каждый запрос независимый."
        notice = ""

    bot.answer_callback_query(call.id, answer)
    try:
        updated_text = (
            f"🔀 <b>Режим разговора</b>\n\n"
            f"Выбрано: {'💬 Чат (с памятью)' if new_mode == 'chat' else '💡 Вопрос-ответ (без памяти)'}\n"
            + (f"\n{notice}" if notice else "")
        )
        bot.edit_message_text(
            updated_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=_mode_keyboard(new_mode),
        )
    except Exception:
        pass


@bot.message_handler(commands=["reset", "clear"])
@with_user_check(bot)
def handle_reset(message):
    """Обработчик команд /reset и /clear — очистка истории разговора."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    current_mode = ctx_svc.get_mode(user_id)
    msg_count = ctx_svc.get_message_count(user_id)

    if current_mode == "single" and msg_count == 0:
        bot.send_message(chat_id, "ℹ️ Ты в режиме <b>Вопрос-ответ</b> — история и так не сохраняется.", parse_mode="HTML")
        return

    if msg_count == 0:
        bot.send_message(chat_id, "ℹ️ История разговора уже пуста.")
        return

    bot.send_message(
        chat_id,
        f"🗑 Очистить историю разговора? ({msg_count} реплик)\n"
        "Это действие нельзя отменить.",
        reply_markup=_clear_confirm_keyboard(user_id),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("ctx_clear_"))
def callback_clear(call):
    parts = call.data.split("_")
    action = parts[2]  # "yes" or "no"
    try:
        owner_id = int(parts[3])
    except (IndexError, ValueError):
        bot.answer_callback_query(call.id, "Ошибка.")
        return

    if call.from_user.id != owner_id:
        bot.answer_callback_query(call.id, "Это не твоя кнопка.", show_alert=True)
        return

    if action == "yes":
        ctx_svc.clear_context(call.from_user.id)
        bot.answer_callback_query(call.id, "История очищена.")
        try:
            bot.edit_message_text(
                "✅ История разговора очищена. Начинаем с чистого листа!",
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception:
            pass
    else:
        bot.answer_callback_query(call.id, "Отмена.")
        try:
            bot.edit_message_text(
                "❌ Очистка отменена. История сохранена.",
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception:
            pass


@bot.message_handler(commands=["memory"])
@with_user_check(bot)
def handle_memory(message):
    """Управление автопамятью: /memory, /memory on, /memory off."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    parts = message.text.split()

    settings = am_svc.get_settings(user_id) or {"enabled": True, "last_suggested_at": None}
    enabled = bool(settings.get("enabled"))

    if len(parts) >= 2:
        arg = parts[1].strip().lower()
        if arg in ("on", "enable", "1", "true", "yes"):
            am_svc.set_enabled(user_id, True)
            bot.send_message(
                chat_id,
                "✅ Автопамять включена. Иногда я буду предлагать, что стоит запомнить.\n"
                "Это всегда требует подтверждения кнопкой.",
            )
            return
        if arg in ("off", "disable", "0", "false", "no"):
            am_svc.set_enabled(user_id, False)
            bot.send_message(
                chat_id,
                "⏸ Автопамять выключена.\n"
                "Ты всё равно можешь сохранять вручную: /remember и /prefer",
            )
            return

    status = "✅ включена" if enabled else "⏸ выключена"
    bot.send_message(
        chat_id,
        "🧠 <b>Автопамять</b>\n\n"
        f"Статус: {status}\n\n"
        "Я могу предлагать сохранить полезные факты/предпочтения из диалога.\n"
        "Сохраняется только после твоего подтверждения.\n\n"
        "<i>Команды:</i>\n"
        "/memory on — включить\n"
        "/memory off — выключить",
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=lambda c: c.data == "mem_na")
def callback_mem_noop(call):
    bot.answer_callback_query(call.id, "Ок.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("mem_"))
def callback_memory(call):
    user_id = call.from_user.id
    data = call.data

    if data.startswith("mem_a_"):
        parts = data.split("_")
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "Ошибка.")
            return
        suggestion_id = parts[2]
        try:
            idx = int(parts[3])
        except ValueError:
            bot.answer_callback_query(call.id, "Ошибка.")
            return

        ok, msg, items = am_svc.apply_suggestion_item(
            telegram_id=user_id,
            suggestion_id=suggestion_id,
            item_index=idx,
        )
        bot.answer_callback_query(call.id, msg)
        if items is not None:
            try:
                bot.edit_message_text(
                    _memory_suggestion_text(items),
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=_memory_keyboard(suggestion_id, items),
                )
            except Exception:
                pass
        return

    if data.startswith("mem_all_"):
        suggestion_id = data.split("_", 2)[2]
        last_msg = "Готово."
        # Try apply all items best-effort
        for i in range(0, 50):
            ok, msg, items = am_svc.apply_suggestion_item(
                telegram_id=user_id,
                suggestion_id=suggestion_id,
                item_index=i,
            )
            if items is None:
                break
            if msg == "Некорректный пункт.":
                break
            last_msg = msg

        bot.answer_callback_query(call.id, last_msg)
        if items is not None:
            try:
                bot.edit_message_text(
                    _memory_suggestion_text(items),
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=_memory_keyboard(suggestion_id, items),
                )
            except Exception:
                pass
        return

    if data.startswith("mem_skip_"):
        suggestion_id = data.split("_", 2)[2]
        am_svc.dismiss_suggestion(telegram_id=user_id, suggestion_id=suggestion_id, status="dismissed")
        bot.answer_callback_query(call.id, "Ок, не буду сейчас.")
        try:
            bot.edit_message_text(
                "⏭ Ок, не буду сохранять. Если захочешь — расскажи сам: /remember или /prefer",
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception:
            pass
        return

    if data.startswith("mem_off_"):
        suggestion_id = data.split("_", 2)[2]
        am_svc.set_enabled(user_id, False)
        am_svc.dismiss_suggestion(telegram_id=user_id, suggestion_id=suggestion_id, status="dismissed")
        bot.answer_callback_query(call.id, "Ок, больше не предлагаю.")
        try:
            bot.edit_message_text(
                "🚫 Понял. Больше не буду предлагать автопамять.\n"
                "Включить обратно можно командой /memory on",
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception:
            pass
        return


@bot.message_handler(func=lambda message: message.text is not None)
@with_user_check(bot)
def handle_text_message(message):
    """
    Обработчик текстовых сообщений от пользователей.
    
    Args:
        message: Объект сообщения от Telegram
    """
    user_message = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    uid_hash = user_id_hash(user_id)
    
    # Пропускаем команды (они обрабатываются отдельными хендлерами)
    if user_message.startswith('/'):
        return

    # Maintenance mode: блокируем запросы обычных пользователей (админы проходят)
    maintenance = get_setting("maintenance_mode", False)
    if isinstance(maintenance, bool):
        is_maintenance = maintenance
    else:
        is_maintenance = str(maintenance).lower() in ("true", "1", "yes")
    if is_maintenance:
        role_weight = getattr(message, "_user", None) and message._user.get("role_weight") or 0
        if role_weight < 100:
            bot.send_message(
                chat_id,
                "🔧 Бот временно на техническом обслуживании. Попробуйте позже.",
            )
            return

    # Проверка лимитов
    from services.limiter import check_limits

    allowed, limit_reason = check_limits(user_id)
    if not allowed:
        bot.send_message(chat_id, limit_reason)
        return

    # ── Agent mode: delegate to "Балабол-новостник" agent loop ───────────────
    if is_agent_enabled(user_id):
        from services.agent_runner import run_agent

        bot.send_chat_action(chat_id, "typing")
        try:
            agent_response = run_agent(user_message, user_id)
        except Exception as agent_err:
            logger.exception(
                "agent_run_failed",
                extra={"event": "agent_run_failed", "user_id_hash": uid_hash,
                       "error_type": type(agent_err).__name__},
            )
            agent_response = f"Агент сломался: {agent_err}"

        send_long_message(
            chat_id,
            agent_response,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        if is_voice_enabled(user_id):
            try:
                voice_key = get_user_voice(user_id)
                ogg_data = synthesize_voice(agent_response, voice_key=voice_key)
                bot.send_voice(chat_id, ogg_data)
            except Exception:
                pass
        return

    try:
        selected_model = get_user_model(user_id)
        context_mode = ctx_svc.get_mode(user_id)

        # Summary (2B): inject into system prompt, not into history messages
        convo_summary = ctx_svc.get_summary(user_id) if context_mode == "chat" else None

        # ── Short memory (C): rolling conversation history ────────────────────
        history = ctx_svc.get_history(user_id) if context_mode == "chat" else []

        # ── Long memory D: personal profile facts ─────────────────────────────
        profile_ctx = profile_svc.build_profile_context(user_id)
        if profile_ctx:
            # Prepend before chat history so it's "background knowledge"
            history = [{"role": "assistant", "content": profile_ctx}] + history

        # ── Long memory C: RAG knowledge base ─────────────────────────────────
        rag_ctx: str | None = None
        if is_kb_enabled(user_id):
            rag_ctx = kb_svc.build_kb_context(user_id, user_message)
            if rag_ctx:
                # Append after history — closest to the user's question
                history = history + [{"role": "assistant", "content": rag_ctx}]

        # ── Persona (role) ─────────────────────────────────────────────────────
        persona_addon = persona_svc.build_persona_addon(user_id)

        # ── Adaptive system message ────────────────────────────────────────────
        system_msg = _build_system_message(
            has_profile=profile_ctx is not None,
            has_kb_context=rag_ctx is not None,
            persona_prompt=persona_addon,
            convo_summary=convo_summary,
        )

        request_id = uuid.uuid4().hex
        logger.info(
            "user_message_received",
            extra={
                "event": "user_message_received",
                "request_id": request_id,
                "user_id_hash": uid_hash,
                "selected_model": selected_model,
                "context_mode": context_mode,
                "history_len": len(history),
                "has_profile": profile_ctx is not None,
                "has_rag": rag_ctx is not None,
                "persona_role": persona_svc.get_user_role(user_id),
                **text_meta(user_message),
            },
        )

        bot_response, cost_usd = get_chat_response(
            user_message,
            model=selected_model,
            history=history,
            system_message=system_msg,
            request_id=request_id,
            user_id_hash=uid_hash,
            telegram_id=user_id,
        )

        # Persist turn to context when in chat mode
        if context_mode == "chat":
            ctx_svc.add_turn(user_id, user_message, bot_response)

        logger.info(
            "user_message_answered",
            extra={
                "event": "user_message_answered",
                "request_id": request_id,
                "user_id_hash": uid_hash,
                "selected_model": selected_model,
                "reply_len": len(bot_response or ""),
                "cost_usd": round(cost_usd, 6),
            },
        )

        send_long_message(chat_id, bot_response)

        # ── Cost footer: show price in RUB if non-zero ─────────────────────────
        cost_rub_str = cbr_svc.format_cost_rub(cost_usd)
        if cost_rub_str:
            bot.send_message(
                chat_id,
                f"💰 <i>Стоимость запроса: {cost_rub_str}</i>",
                parse_mode="HTML",
            )

        # TTS voice response if enabled
        if is_voice_enabled(user_id):
            try:
                voice_key = get_user_voice(user_id)
                ogg_data = synthesize_voice(bot_response, voice_key=voice_key)
                bot.send_voice(chat_id, ogg_data)
                logger.info(
                    "voice_sent",
                    extra={
                        "event": "voice_sent",
                        "request_id": request_id,
                        "user_id_hash": uid_hash,
                        "voice": voice_key,
                        "ogg_size": len(ogg_data),
                    },
                )
            except Exception as tts_err:
                logger.warning(
                    "voice_failed",
                    extra={
                        "event": "voice_failed",
                        "request_id": request_id,
                        "user_id_hash": uid_hash,
                        "error_type": type(tts_err).__name__,
                        "error": str(tts_err)[:200],
                    },
                )
                bot.send_message(chat_id, f"🔇 Не удалось озвучить ответ: {tts_err}")

        # Context mode hint (only in single/stateless mode — show briefly as footer)
        if context_mode == "single":
            bot.send_message(
                chat_id,
                "ℹ️ <i>Режим: Вопрос-ответ. Память не сохраняется. Переключи /mode чтобы включить чат.</i>",
                parse_mode="HTML",
            )

        # ── Useful long-term memory: suggest facts/preferences (Idea 3) ───────
        if context_mode == "chat":
            try:
                suggestion = am_svc.maybe_create_suggestion(
                    telegram_id=user_id,
                    selected_model=selected_model,
                )
                if suggestion:
                    suggestion_id, items = suggestion
                    bot.send_message(
                        chat_id,
                        _memory_suggestion_text(items),
                        parse_mode="HTML",
                        reply_markup=_memory_keyboard(suggestion_id, items),
                    )
            except Exception as mem_err:
                logger.warning(
                    "auto_memory_suggest_failed",
                    extra={
                        "event": "auto_memory_suggest_failed",
                        "user_id_hash": uid_hash,
                        "error": str(mem_err)[:200],
                    },
                )

    except Exception as e:
        logger.exception(
            "handle_message_failed",
            extra={
                "event": "handle_message_failed",
                "user_id_hash": uid_hash,
                "error_type": type(e).__name__,
            },
        )
        # В случае ошибки отправляем пользователю сообщение об ошибке
        try:
            error_message = f"Упс, что-то пошло не так! Ошибка: {str(e)}"
            bot.send_message(chat_id, error_message)
        except Exception:
            # Если не удалось отправить сообщение об ошибке, просто логируем
            print(f"Ошибка при обработке сообщения: {e}")


def main():
    """Главная функция для запуска бота."""
    logger.info("Бот Blabber запущен и готов к работе!")

    # В проде long-polling к Telegram иногда отваливается по сети/таймаутам.
    # Лучше переживать это бесконечным retry, чтобы процесс не падал и не плодил stacktrace.
    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                skip_pending=True,
            )
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            logger.warning("Проблема сети при long-polling к Telegram: %s. Повтор через 1с...", e)
            time.sleep(1)
        except Exception:
            logger.exception("Неожиданная ошибка в polling. Перезапуск через 5с...")
            time.sleep(5)


if __name__ == "__main__":
    main()

