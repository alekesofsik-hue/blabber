"""
Универсальный модуль для работы с OpenAI API (GPT-4o, GPT-4o-mini и др.).

Переменные окружения:
    - OPENAI_API_KEY — API ключ OpenAI
    - OPENAI_MODEL — модель (по умолчанию: gpt-4o-mini)

Пример:
    from llm_providers.openai import get_response

    text = get_response(
        message="Привет!",
        system_message="Ты — балабол..."
    )
"""

import os
from typing import Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

from services.config_registry import get_setting

load_dotenv()


def get_response(
    message: str,
    system_message: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Получить ответ от OpenAI API (GPT-4o, GPT-4o-mini и др.).

    Args:
        message: Сообщение пользователя
        system_message: Системное сообщение для настройки поведения модели
        **kwargs:
            - api_key: API ключ (или OPENAI_API_KEY)
            - model: модель (или OPENAI_MODEL / get_setting)
            - temperature: температура генерации (по умолчанию 0.8)
            - max_tokens: макс. токенов (по умолчанию 2000)
            - history: список {"role", "content"} для контекста диалога
            - usage_out: dict — если передан, заполняется реальными tokens_in/tokens_out

    Returns:
        Ответ модели (str)
    """
    api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY не установлен. "
            "Укажите api_key в kwargs или установите OPENAI_API_KEY в .env"
        )

    model = (
        kwargs.get("model")
        or get_setting("openai_model", "gpt-4o-mini", env_key="OPENAI_MODEL")
    )
    temperature = float(kwargs.get("temperature", 0.8))
    max_tokens = int(kwargs.get("max_tokens", 2000))
    history: list = kwargs.get("history") or []
    usage_out: Optional[dict] = kwargs.get("usage_out")

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    client = OpenAI(api_key=api_key)

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
        return chat_completion.choices[0].message.content or ""
    except Exception as e:
        raise Exception(f"Ошибка при обращении к OpenAI API: {e}") from e
