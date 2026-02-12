"""
Telegram-бот Blabber — балабол, который любит трепаться и болтать.
"""

import logging
import os
import time
import uuid
import telebot
import requests
from dotenv import load_dotenv
from utils import get_chat_response
from user_storage import (
    get_user_model, set_user_model, get_available_models,
    is_voice_enabled, set_voice_enabled,
    get_user_voice, set_user_voice,
)
from telemetry import setup_telemetry, text_meta, user_id_hash
from tts import synthesize_voice, get_available_voices


# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен в переменных окружения")

# Создаем экземпляр бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

logger = setup_telemetry("blabber")

# Лимит Telegram на длину одного сообщения
TG_MSG_LIMIT = 4096


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


@bot.message_handler(commands=['start'])
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
    
    welcome_text = (
        "Привет! Я Blabber — балабол, который любит трепаться и болтать! 😄\n\n"
        "Я умею общаться используя разные модели:\n"
        "• GigaChat\n"
        "• OpenRouter (DeepSeek)\n"
        "• DeepSeek R1 (рассуждающая)\n"
        "• Yandex GPT\n"
        "• Ollama (local)\n\n"
        "Используй команды:\n"
        "/models - список доступных моделей\n"
        "/model <название> - переключить модель\n"
        "/voice - управление озвучкой ответов 🔊\n"
        "/help - помощь\n\n"
        f"Сейчас используется модель: {get_available_models().get(get_user_model(user_id), 'неизвестна')}"
    )
    
    bot.send_message(chat_id, welcome_text)


@bot.message_handler(commands=['help'])
def handle_help(message):
    """Обработчик команды /help"""
    chat_id = message.chat.id

    logger.info(
        "command_help",
        extra={
            "event": "command_help",
        },
    )
    
    help_text = (
        "📚 Команды бота:\n\n"
        "/start - начать работу\n"
        "/models - показать доступные модели\n"
        "/model <название> - переключить модель\n"
        "   Примеры:\n"
        "   /model gigachat - переключить на GigaChat\n"
        "   /model openrouter - переключить на OpenRouter (DeepSeek)\n"
        "   /model reasoning - переключить на DeepSeek R1 (рассуждающая)\n"
        "   /model yandexgpt - переключить на Yandex GPT\n"
        "   /model ollama - переключить на Ollama (local)\n"
        "/voice - управление озвучкой ответов 🔊\n"
        "   /voice on - включить озвучку\n"
        "   /voice off - выключить озвучку\n"
        "   /voice alena - женский (Алёна)\n"
        "   /voice filipp - мужской (Филипп)\n"
        "/help - показать эту справку\n\n"
        "Просто напиши мне что-нибудь, и я отвечу как балабол! 😊"
    )
    
    bot.send_message(chat_id, help_text)


@bot.message_handler(commands=['models'])
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
    models_text += "\nИспользуй /model <название> для переключения"
    
    bot.send_message(chat_id, models_text)


@bot.message_handler(commands=['model'])
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


@bot.message_handler(commands=['voice'])
def handle_voice(message):
    """
    Обработчик команды /voice — управление голосовыми ответами.

    /voice          — показать текущее состояние
    /voice on       — включить озвучку
    /voice off      — выключить озвучку
    /voice svetlana — сменить голос на Светлану (женский)
    /voice dmitry   — сменить голос на Дмитрия (мужской)
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


@bot.message_handler(func=lambda message: message.text is not None)
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
    
    try:
        # Получаем выбранную модель пользователя
        selected_model = get_user_model(user_id)

        request_id = uuid.uuid4().hex
        logger.info(
            "user_message_received",
            extra={
                "event": "user_message_received",
                "request_id": request_id,
                "user_id_hash": uid_hash,
                "selected_model": selected_model,
                **text_meta(user_message),
            },
        )
        
        # Отправляем сообщение в выбранную модель и получаем ответ
        bot_response = get_chat_response(
            user_message,
            model=selected_model,
            request_id=request_id,
            user_id_hash=uid_hash,
        )

        logger.info(
            "user_message_answered",
            extra={
                "event": "user_message_answered",
                "request_id": request_id,
                "user_id_hash": uid_hash,
                "selected_model": selected_model,
                "reply_len": len(bot_response or ""),
            },
        )
        
        # Отправляем ответ пользователю (с разбиением, если текст длинный)
        send_long_message(chat_id, bot_response)

        # Отправляем голосовое сообщение, если озвучка включена
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
                bot.send_message(
                    chat_id,
                    f"🔇 Не удалось озвучить ответ: {tts_err}",
                )

        # Отправляем краткое напоминание о том, что контекст не сохраняется
        context_notice = "ℹ️ <i>Контекст не сохраняется. Каждое сообщение обрабатывается отдельно.</i>"
        bot.send_message(chat_id, context_notice, parse_mode="HTML")
        
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

