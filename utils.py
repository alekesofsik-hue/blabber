"""
Утилиты для работы с OpenRouter API, GigaChat API, Yandex GPT API и Ollama (local).

Этот модуль обеспечивает обратную совместимость с существующим кодом бота.
Внутри используются универсальные модули из llm_providers.

Для новых проектов рекомендуется использовать модули из llm_providers напрямую:
    from llm_providers.openrouter import get_response
    from llm_providers.gigachat import get_response
    from llm_providers.yandexgpt import get_response
"""

import os
import time
import logging
from dotenv import load_dotenv

# Импортируем новые универсальные модули
from llm_providers.openrouter import get_response as openrouter_get_response
from llm_providers.gigachat import get_response as gigachat_get_response
from llm_providers.yandexgpt import get_response as yandexgpt_get_response
from llm_providers.ollama import get_response as ollama_get_response

load_dotenv()

# Системное сообщение "балабола" по умолчанию
DEFAULT_SYSTEM_MESSAGE = (
    "Ты — балабол, любишь много говорить, трепаться и болтать. "
    "Ты не всегда прав, можешь давать пустую болтовню, но всегда дружелюбен и шутлив. "
    "Отвечай многословно, с юмором, иногда отвлекаясь на разные темы."
)


def get_chat_response(
    user_message: str,
    model: str = 'openrouter',
    *,
    request_id: str | None = None,
    user_id_hash: str | None = None,
) -> str:
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
    logger = logging.getLogger("blabber")
    t0 = time.monotonic()

    logger.info(
        "llm_request_started",
        extra={
            "event": "llm_request_started",
            "request_id": request_id,
            "user_id_hash": user_id_hash,
            "provider": model,
        },
    )
    
    try:
        if model == 'gigachat':
            result = gigachat_get_response(
                message=user_message,
                system_message=system_message
            )
        elif model == 'yandexgpt':
            result = yandexgpt_get_response(
                message=user_message,
                system_message=system_message
            )
        elif model == 'ollama':
            result = ollama_get_response(
                message=user_message,
                system_message=system_message
            )
        elif model == 'openrouter':
            result = openrouter_get_response(
                message=user_message,
                system_message=system_message
            )
        else:
            raise ValueError(
                f"Неизвестная модель: {model}. "
                f"Доступные: gigachat, openrouter, yandexgpt, ollama"
            )

        dt_ms = int((time.monotonic() - t0) * 1000)
        logger.info(
            "llm_request_finished",
            extra={
                "event": "llm_request_finished",
                "request_id": request_id,
                "user_id_hash": user_id_hash,
                "provider": model,
                "duration_ms": dt_ms,
                "reply_len": len(result or ""),
                "success": True,
            },
        )
        return result

    except Exception as e:
        dt_ms = int((time.monotonic() - t0) * 1000)
        logger.exception(
            "llm_request_failed",
            extra={
                "event": "llm_request_failed",
                "request_id": request_id,
                "user_id_hash": user_id_hash,
                "provider": model,
                "duration_ms": dt_ms,
                "success": False,
                "error_type": type(e).__name__,
            },
        )
        raise
