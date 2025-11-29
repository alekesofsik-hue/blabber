"""
Telegram-бот Blabber — балабол, который любит трепаться и болтать.
"""

import os
import telebot
from dotenv import load_dotenv
from utils import get_chat_response
from user_storage import get_user_model, set_user_model, get_available_models


# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен в переменных окружения")

# Создаем экземпляр бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработчик команды /start"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    welcome_text = (
        "Привет! Я Blabber — балабол, который любит трепаться и болтать! 😄\n\n"
        "Я умею общаться используя разные модели:\n"
        "• GigaChat\n"
        "• OpenRouter (DeepSeek)\n"
        "• Yandex GPT\n\n"
        "Используй команды:\n"
        "/models - список доступных моделей\n"
        "/model <название> - переключить модель\n"
        "/help - помощь\n\n"
        f"Сейчас используется модель: {get_available_models().get(get_user_model(user_id), 'неизвестна')}"
    )
    
    bot.send_message(chat_id, welcome_text)


@bot.message_handler(commands=['help'])
def handle_help(message):
    """Обработчик команды /help"""
    chat_id = message.chat.id
    
    help_text = (
        "📚 Команды бота:\n\n"
        "/start - начать работу\n"
        "/models - показать доступные модели\n"
        "/model <название> - переключить модель\n"
        "   Примеры:\n"
        "   /model gigachat - переключить на GigaChat\n"
        "   /model openrouter - переключить на OpenRouter (DeepSeek)\n"
        "   /model yandexgpt - переключить на Yandex GPT\n"
        "/help - показать эту справку\n\n"
        "Просто напиши мне что-нибудь, и я отвечу как балабол! 😊"
    )
    
    bot.send_message(chat_id, help_text)


@bot.message_handler(commands=['models'])
def handle_models(message):
    """Обработчик команды /models - показать доступные модели"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
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
            "/model yandexgpt\n\n"
            "Используй /models чтобы увидеть список доступных моделей"
        )
        return
    
    model_name = parts[1].lower()
    available_models = get_available_models()
    
    if model_name not in available_models:
        bot.send_message(
            chat_id,
            f"❌ Модель '{model_name}' не найдена!\n\n"
            f"Доступные модели: {', '.join(available_models.keys())}\n"
            "Используй /models чтобы увидеть список"
        )
        return
    
    # Устанавливаем модель
    if set_user_model(user_id, model_name):
        bot.send_message(
            chat_id,
            f"✅ Модель переключена на: {available_models[model_name]}\n\n"
            "Теперь я буду использовать эту модель для ответов!"
        )
    else:
        bot.send_message(chat_id, "❌ Ошибка при переключении модели")


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
    
    # Пропускаем команды (они обрабатываются отдельными хендлерами)
    if user_message.startswith('/'):
        return
    
    try:
        # Получаем выбранную модель пользователя
        selected_model = get_user_model(user_id)
        
        # Отправляем сообщение в выбранную модель и получаем ответ
        bot_response = get_chat_response(user_message, model=selected_model)
        
        # Отправляем ответ пользователю
        bot.send_message(chat_id, bot_response)
        
        # Отправляем краткое напоминание о том, что контекст не сохраняется
        context_notice = "ℹ️ <i>Контекст не сохраняется. Каждое сообщение обрабатывается отдельно.</i>"
        bot.send_message(chat_id, context_notice, parse_mode='HTML')
        
    except Exception as e:
        # В случае ошибки отправляем пользователю сообщение об ошибке
        try:
            error_message = f"Упс, что-то пошло не так! Ошибка: {str(e)}"
            bot.send_message(chat_id, error_message)
        except Exception:
            # Если не удалось отправить сообщение об ошибке, просто логируем
            print(f"Ошибка при обработке сообщения: {e}")


def main():
    """Главная функция для запуска бота."""
    print("Бот Blabber запущен и готов к работе!")
    bot.infinity_polling()


if __name__ == "__main__":
    main()

