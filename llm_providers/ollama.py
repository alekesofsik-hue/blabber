"""
Универсальный модуль для работы с Ollama (локальная LLM через HTTP API).

По умолчанию рассчитан на сценарий "без контекста": отправляем только system + user.

Переменные окружения:
    - OLLAMA_BASE_URL (по умолчанию: http://127.0.0.1:11434)
    - OLLAMA_MODEL (по умолчанию: qwen2.5:3b-instruct-q4_K_M)

Пример:
    from llm_providers.ollama import get_response

    text = get_response(
        message="Привет! Ответь по-русски, многословно.",
        system_message="Ты — балабол..."
    )
"""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

try:
    import httpx
except ImportError:
    httpx = None

try:
    import requests
except ImportError:
    requests = None


def _build_options(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Собирает options для Ollama из kwargs, отфильтровывая None.
    Поддерживаем самые полезные параметры для скорости/качества.
    """
    # Важно для слабого CPU: по умолчанию ограничиваем длину ответа,
    # иначе "балабол" может генерировать слишком долго и клиент словит timeout.
    env_num_predict = os.getenv("OLLAMA_NUM_PREDICT")
    try:
        env_num_predict_int = int(env_num_predict) if env_num_predict else None
    except ValueError:
        env_num_predict_int = None

    env_num_ctx = os.getenv("OLLAMA_NUM_CTX")
    try:
        env_num_ctx_int = int(env_num_ctx) if env_num_ctx else None
    except ValueError:
        env_num_ctx_int = None

    options = {
        "temperature": kwargs.get("temperature", 0.8),
        "num_predict": kwargs.get("num_predict", env_num_predict_int),
        "num_ctx": kwargs.get("num_ctx", env_num_ctx_int),
        "top_p": kwargs.get("top_p"),
        "top_k": kwargs.get("top_k"),
        "repeat_penalty": kwargs.get("repeat_penalty"),
        "seed": kwargs.get("seed"),
    }
    return {k: v for k, v in options.items() if v is not None}


def get_response(
    message: str,
    system_message: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Получить ответ от локального Ollama.

    Args:
        message: Сообщение пользователя
        system_message: Системное сообщение для настройки поведения модели
        **kwargs:
            - base_url: базовый URL Ollama (или OLLAMA_BASE_URL)
            - model: имя модели Ollama (или OLLAMA_MODEL)
            - timeout: таймаут (сек), по умолчанию 60
            - temperature: температура генерации
            - num_predict: ограничение длины ответа (токены)
            - num_ctx: размер контекста
            - top_p/top_k/repeat_penalty/seed: доп. параметры sampling

    Returns:
        Ответ модели (str)
    """
    base_url = kwargs.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = kwargs.get("model") or os.getenv("OLLAMA_MODEL", "gemma2:2b-instruct-q4_K_M")
    timeout = float(kwargs.get("timeout") or os.getenv("OLLAMA_TIMEOUT", "180"))

    if httpx is None and requests is None:
        raise RuntimeError("Для Ollama нужен httpx или requests. Установите: pip install httpx")

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": message})

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": _build_options(kwargs),
    }

    url = f"{base_url.rstrip('/')}/api/chat"

    try:
        if httpx is not None:
            # Разделяем таймауты: подключение обычно быстрое, а чтение (генерация) может быть долгим.
            httpx_timeout = httpx.Timeout(timeout=timeout, connect=5.0)
            with httpx.Client(timeout=httpx_timeout) as client:
                r = client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
        else:
            r = requests.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            data = r.json()

        # Ollama chat response format:
        # { "message": { "role": "assistant", "content": "..." }, ... }
        msg = data.get("message") or {}
        content = msg.get("content")
        if not content:
            raise ValueError(f"Пустой ответ от Ollama: {data}")
        return content

    except Exception as e:
        raise Exception(f"Ошибка при обращении к Ollama ({url}, model={model}): {e}")

