"""
Утилиты для работы с OpenRouter API, GigaChat API и Yandex GPT API.

Этот модуль обеспечивает обратную совместимость с существующим кодом бота.
Внутри используются универсальные модули из llm_providers.

Для новых проектов рекомендуется использовать модули из llm_providers напрямую:
    from llm_providers.openrouter import get_response
    from llm_providers.gigachat import get_response
    from llm_providers.yandexgpt import get_response
"""

import os
from dotenv import load_dotenv

# Импортируем новые универсальные модули
from llm_providers.openrouter import get_response as openrouter_get_response
from llm_providers.gigachat import get_response as gigachat_get_response
from llm_providers.yandexgpt import get_response as yandexgpt_get_response

load_dotenv()

# Системное сообщение "балабола" по умолчанию
DEFAULT_SYSTEM_MESSAGE = (
    "Ты — балабол, любишь много говорить, трепаться и болтать. "
    "Ты не всегда прав, можешь давать пустую болтовню, но всегда дружелюбен и шутлив. "
    "Отвечай многословно, с юмором, иногда отвлекаясь на разные темы."
)


def get_chat_response(user_message: str, model: str = 'openrouter') -> str:
    """
    Получить ответ от выбранной модели с заданным стилем "балабола".
    
    Это функция для обратной совместимости. Она использует новые модули из llm_providers.
    
    Args:
        user_message: Сообщение от пользователя
        model: Модель для генерации ('gigachat', 'openrouter' или 'yandexgpt')
        
    Returns:
        Ответ от модели
    
    Raises:
        ValueError: Если указана неизвестная модель
        Exception: При ошибке обращения к API
    """
    system_message = DEFAULT_SYSTEM_MESSAGE
    
    if model == 'gigachat':
        return gigachat_get_response(
            message=user_message,
            system_message=system_message
        )
    elif model == 'yandexgpt':
        return yandexgpt_get_response(
            message=user_message,
            system_message=system_message
        )
    elif model == 'openrouter':
        return openrouter_get_response(
            message=user_message,
            system_message=system_message
        )
    else:
        raise ValueError(
            f"Неизвестная модель: {model}. "
            f"Доступные: gigachat, openrouter, yandexgpt"
        )
