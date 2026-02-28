"""
Универсальный модуль для работы с OpenRouter API.

Использование:
    from llm_providers.openrouter import get_response
    
    response = get_response(
        message="Привет!",
        system_message="Ты помощник",
        model="deepseek/deepseek-chat",
        api_key="your_key"
    )
"""

import os
from typing import Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_response(
    message: str,
    system_message: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Получить ответ от OpenRouter API (DeepSeek и другие модели).

    Args:
        message: Сообщение пользователя
        system_message: Системное сообщение для настройки поведения модели
        **kwargs: Дополнительные параметры:
            - api_key: API ключ (если не указан, берётся из PROXY_API_KEY)
            - base_url: URL API (по умолчанию: https://api.proxyapi.ru/openrouter/v1)
            - model: Название модели (по умолчанию: deepseek/deepseek-chat)
            - temperature: Температура генерации (по умолчанию: 0.8)
            - max_tokens: Максимальное количество токенов (по умолчанию: 2000)
            - history: список {"role", "content"} для контекста диалога
            - usage_out: dict — если передан, заполняется реальными tokens_in/tokens_out

    Returns:
        Ответ от модели в виде строки

    Raises:
        ValueError: Если API ключ не указан
        Exception: При ошибке обращения к API
    """
    api_key = kwargs.get('api_key') or os.getenv("PROXY_API_KEY")
    base_url = kwargs.get('base_url', "https://api.proxyapi.ru/openrouter/v1")
    model = kwargs.get('model', "deepseek/deepseek-chat")
    temperature = kwargs.get('temperature', 0.8)
    max_tokens = kwargs.get('max_tokens', 2000)
    history: list = kwargs.get('history') or []
    usage_out: Optional[dict] = kwargs.get('usage_out')

    if not api_key:
        raise ValueError(
            "PROXY_API_KEY не установлен. "
            "Укажите api_key в kwargs или установите PROXY_API_KEY в .env"
        )

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if usage_out is not None and chat_completion.usage:
            usage_out["tokens_in"] = chat_completion.usage.prompt_tokens
            usage_out["tokens_out"] = chat_completion.usage.completion_tokens
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Ошибка при обращении к OpenRouter API: {e}") from e

