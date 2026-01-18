"""
Универсальный модуль для работы с GigaChat API.

Использование:
    from llm_providers.gigachat import get_response
    
    response = get_response(
        message="Привет!",
        system_message="Ты помощник",
        credentials="client_id:client_secret"
    )
"""

import os
import time
from typing import Optional
from dotenv import load_dotenv

from .gigachat_token import get_gigachat_token_info

try:
    import httpx
except ImportError:
    try:
        import requests
        httpx = None
    except ImportError:
        httpx = None
        requests = None

load_dotenv()

# Кэш токена GigaChat
_token_cache = {
    'token': None,
    'expires_at': 0
}

# URL для GigaChat API
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


def _get_access_token(credentials: Optional[str] = None, verify_ssl: Optional[bool] = None) -> str:
    """
    Получить токен доступа GigaChat с кэшированием.
    
    Args:
        credentials: Ключ авторизации (если не указан, берётся из GIGACHAT_CREDENTIALS)
        verify_ssl: Проверять SSL сертификат (если не указан, берётся из GIGACHAT_VERIFY_SSL)
    
    Returns:
        Токен доступа GigaChat
    """
    global _token_cache
    current_time = int(time.time())
    
    # Если токен ещё валиден, возвращаем его
    if _token_cache['token'] and _token_cache['expires_at'] > current_time:
        return _token_cache['token']
    
    # Получаем новый токен
    # Если verify_ssl не указан, используем значение из переменных окружения
    if verify_ssl is None:
        verify_ssl_str = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower()
        verify_ssl = verify_ssl_str in ("true", "1", "yes", "on")
    
    token, expires_in_seconds, expires_datetime = get_gigachat_token_info(
        credentials=credentials,
        verify_ssl=verify_ssl
    )
    
    # Сохраняем в кэш (оставляем запас в 60 секунд)
    _token_cache['token'] = token
    _token_cache['expires_at'] = current_time + expires_in_seconds - 60
    
    return token


def get_response(
    message: str,
    system_message: Optional[str] = None,
    **kwargs
) -> str:
    """
    Получить ответ от GigaChat API.
    
    Args:
        message: Сообщение пользователя
        system_message: Системное сообщение для настройки поведения модели
        **kwargs: Дополнительные параметры:
            - credentials: Ключ авторизации (если не указан, берётся из GIGACHAT_CREDENTIALS)
            - verify_ssl: Проверять SSL сертификат (по умолчанию: False)
            - model: Название модели (по умолчанию: GigaChat)
            - timeout: Таймаут запроса в секундах (по умолчанию: 60)
    
    Returns:
        Ответ от модели в виде строки
    
    Raises:
        ValueError: Если credentials не указаны
        Exception: При ошибке обращения к API
    """
    if not httpx and not requests:
        raise Exception(
            "Требуется библиотека httpx или requests для работы с GigaChat API. "
            "Установите одну из них: pip install httpx или pip install requests"
        )
    
    # Получаем параметры из kwargs или переменных окружения
    credentials = kwargs.get('credentials') or os.getenv("GIGACHAT_CREDENTIALS")
    verify_ssl = kwargs.get('verify_ssl')
    if verify_ssl is None:
        verify_ssl_str = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower()
        verify_ssl = verify_ssl_str in ("true", "1", "yes", "on")
    model = kwargs.get('model', 'GigaChat')
    timeout = kwargs.get('timeout', 60.0)
    
    if not credentials:
        raise ValueError(
            "GIGACHAT_CREDENTIALS не установлен. "
            "Укажите credentials в kwargs или установите GIGACHAT_CREDENTIALS в .env"
        )
    
    # Получаем токен доступа
    access_token = _get_access_token(credentials, verify_ssl)
    
    # Формируем сообщения
    messages = []
    if system_message:
        messages.append({'role': 'system', 'content': system_message})
    messages.append({'role': 'user', 'content': message})
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    payload = {
        'model': model,
        'messages': messages,
        'stream': False
    }
    
    try:
        if httpx:
            with httpx.Client(verify=verify_ssl, timeout=timeout) as client:
                response = client.post(
                    GIGACHAT_API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
        else:
            response = requests.post(
                GIGACHAT_API_URL,
                headers=headers,
                json=payload,
                verify=verify_ssl,
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
        
        # Извлекаем ответ из структуры ответа GigaChat
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            raise ValueError("Пустой ответ от GigaChat API")
            
    except Exception as e:
        error_str = str(e)
        # Если токен истёк (401), очищаем кэш и пробуем ещё раз (только один раз)
        if ('401' in error_str or 'Unauthorized' in error_str) and _token_cache['token']:
            _token_cache['token'] = None
            _token_cache['expires_at'] = 0
            # Рекурсивный вызов, но только один раз благодаря проверке _token_cache['token']
            return get_response(message, system_message, **kwargs)
        raise Exception(f"Ошибка при обращении к GigaChat API: {error_str}") from e

