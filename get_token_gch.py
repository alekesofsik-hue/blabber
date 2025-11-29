"""
Универсальный модуль для получения токена GigaChat API.

Использует прямой HTTP запрос (аналог curl команды) для получения токена.
Работает как curl команда с правильными заголовками и параметрами.

Использование как модуль:
    from get_token_gch import get_gigachat_token, get_gigachat_token_dict, get_gigachat_token_info
    
    # Получить только токен доступа
    token = get_gigachat_token()  
    
    # Получить полный ответ с expires_at и вычисленными значениями
    token_data = get_gigachat_token_dict()
    
    # Получить три значения: токен, секунды до истечения, datetime истечения
    token, seconds_left, expires_datetime = get_gigachat_token_info()

Использование как скрипт:
    python get_token_gch.py
"""

import os
import sys
import json
import base64
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

try:
    import httpx
except ImportError:
    try:
        import requests
        httpx = None
    except ImportError:
        print("Ошибка: требуется библиотека httpx или requests.")
        print("Установите одну из них: pip install httpx или pip install requests")
        sys.exit(1)


# Загружаем переменные окружения из .env файла
load_dotenv()

# URL для получения токена GigaChat
GIGACHAT_TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"


def _get_gigachat_token_direct(credentials: str, verify_ssl: bool = False) -> Dict[str, Any]:
    """
    Получить токен GigaChat напрямую через HTTP запрос (аналог curl).
    
    Args:
        credentials: Ключ авторизации (client_id:client_secret или base64 строка)
        verify_ssl: Проверять SSL сертификат
        
    Returns:
        Словарь с access_token и expires_at
    """
    # Генерируем UUID для RqUID
    rquid = str(uuid.uuid4())
    
    # Подготовка Authorization заголовка
    # Если credentials содержит ':', то это client_id:client_secret
    if ':' in credentials and not credentials.startswith('Basic '):
        # Это client_id:client_secret, нужно закодировать в base64
        auth_string = base64.b64encode(credentials.encode()).decode()
    elif credentials.startswith('Basic '):
        # Уже готовый Basic токен
        auth_string = credentials.replace('Basic ', '')
    else:
        # Предполагаем, что это уже base64 строка
        auth_string = credentials
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rquid,
        'Authorization': f'Basic {auth_string}'
    }
    
    data = {
        'scope': 'GIGACHAT_API_PERS'
    }
    
    # Отключаем предупреждения SSL
    if not verify_ssl:
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning, module='urllib3')
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    try:
        if httpx:
            # Используем httpx
            with httpx.Client(verify=verify_ssl, timeout=30.0) as client:
                response = client.post(
                    GIGACHAT_TOKEN_URL,
                    headers=headers,
                    data=data
                )
                response.raise_for_status()
                return response.json()
        else:
            # Используем requests
            import requests
            response = requests.post(
                GIGACHAT_TOKEN_URL,
                headers=headers,
                data=data,
                verify=verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise Exception(f"Ошибка при получении токена GigaChat: {str(e)}")


def get_gigachat_token(credentials: Optional[str] = None, verify_ssl: Optional[bool] = None) -> str:
    """
    Получить токен доступа GigaChat API.
    
    Args:
        credentials: Ключ авторизации GigaChat (client_id:client_secret или base64 строка). 
                    Если не указан, берётся из переменной окружения GIGACHAT_CREDENTIALS.
        verify_ssl: Проверять SSL сертификат. Если None, берётся из 
                   GIGACHAT_VERIFY_SSL (по умолчанию False из-за проблем с сертификатами).
        
    Returns:
        Токен доступа (access_token).
        
    Raises:
        ValueError: Если credentials не указан и не найден в переменных окружения.
        Exception: Если произошла ошибка при получении токена.
    """
    if credentials is None:
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
    
    if not credentials:
        raise ValueError(
            "GIGACHAT_CREDENTIALS не указан. "
            "Укажите его в параметре credentials или в переменной окружения GIGACHAT_CREDENTIALS"
        )
    
    # Определяем, нужно ли проверять SSL сертификат (по умолчанию False из-за проблем)
    if verify_ssl is None:
        verify_ssl_env = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower()
        verify_ssl = verify_ssl_env in ("true", "1", "yes", "on")
    
    try:
        result = _get_gigachat_token_direct(credentials, verify_ssl)
        access_token = result.get("access_token")
        
        if not access_token:
            raise ValueError("Токен доступа не найден в ответе API")
        
        return access_token
        
    except Exception as e:
        raise Exception(f"Ошибка при получении токена GigaChat: {str(e)}")


def get_gigachat_token_dict(credentials: Optional[str] = None, verify_ssl: Optional[bool] = None) -> Dict[str, Any]:
    """
    Получить полный ответ с токеном доступа и временем истечения GigaChat API.
    
    Args:
        credentials: Ключ авторизации GigaChat (client_id:client_secret или base64 строка).
                    Если не указан, берётся из переменной окружения GIGACHAT_CREDENTIALS.
        verify_ssl: Проверять SSL сертификат. Если None, берётся из 
                   GIGACHAT_VERIFY_SSL (по умолчанию False из-за проблем с сертификатами).
        
    Returns:
        Словарь с ключами:
        - access_token: Токен доступа
        - expires_at: Время истечения токена в миллисекундах (timestamp)
        - expires_in_seconds: Секунды до истечения токена
        - expires_at_datetime: Время истечения в формате datetime
        
    Raises:
        ValueError: Если credentials не указан и не найден в переменных окружения.
        Exception: Если произошла ошибка при получении токена.
    """
    if credentials is None:
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
    
    if not credentials:
        raise ValueError(
            "GIGACHAT_CREDENTIALS не указан. "
            "Укажите его в параметре credentials или в переменной окружения GIGACHAT_CREDENTIALS"
        )
    
    # Определяем, нужно ли проверять SSL сертификат (по умолчанию False из-за проблем)
    if verify_ssl is None:
        verify_ssl_env = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower()
        verify_ssl = verify_ssl_env in ("true", "1", "yes", "on")
    
    try:
        result = _get_gigachat_token_direct(credentials, verify_ssl)
        
        if "access_token" not in result or not result["access_token"]:
            raise ValueError("Токен доступа не найден в ответе API")
        
        # Получаем expires_at в миллисекундах
        expires_at_ms = result.get("expires_at")
        
        if expires_at_ms:
            # Вычисляем секунды до истечения
            current_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            expires_in_seconds = max(0, (expires_at_ms - current_time_ms) // 1000)
            
            # Преобразуем expires_at в datetime
            expires_at_datetime = datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc)
            
            # Добавляем вычисленные значения
            result["expires_in_seconds"] = expires_in_seconds
            result["expires_at_datetime"] = expires_at_datetime
        else:
            result["expires_in_seconds"] = None
            result["expires_at_datetime"] = None
        
        return result
        
    except Exception as e:
        raise Exception(f"Ошибка при получении токена GigaChat: {str(e)}")


def get_gigachat_token_info(credentials: Optional[str] = None, verify_ssl: Optional[bool] = None) -> Tuple[str, int, datetime]:
    """
    Получить три значения: токен доступа, секунды до истечения и время истечения.
    
    Args:
        credentials: Ключ авторизации GigaChat (client_id:client_secret или base64 строка).
                    Если не указан, берётся из переменной окружения GIGACHAT_CREDENTIALS.
        verify_ssl: Проверять SSL сертификат. Если None, берётся из 
                   GIGACHAT_VERIFY_SSL (по умолчанию False из-за проблем с сертификатами).
        
    Returns:
        Кортеж из трёх значений:
        - access_token (str): Токен доступа
        - expires_in_seconds (int): Секунды до истечения токена
        - expires_at_datetime (datetime): Время истечения в формате datetime
        
    Raises:
        ValueError: Если credentials не указан и не найден в переменных окружения.
        Exception: Если произошла ошибка при получении токена.
    """
    token_data = get_gigachat_token_dict(credentials, verify_ssl)
    
    access_token = token_data["access_token"]
    expires_in_seconds = token_data.get("expires_in_seconds", 0)
    expires_at_datetime = token_data.get("expires_at_datetime")
    
    if expires_at_datetime is None:
        raise ValueError("Не удалось определить время истечения токена")
    
    return access_token, expires_in_seconds, expires_at_datetime


def main():
    """
    Главная функция для запуска модуля как скрипта.
    Выводит токен и информацию о нём в консоль.
    """
    try:
        # Получаем три значения: токен, секунды до истечения, datetime истечения
        token, seconds_left, expires_datetime = get_gigachat_token_info()
        
        # Выводим результат
        print("="*60)
        print("ТОКЕН GIGACHAT API")
        print("="*60)
        print(f"\nТокен доступа:")
        print(f"{token}")
        print(f"\nСекунд до истечения: {seconds_left}")
        print(f"\nВремя истечения (UTC): {expires_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Время истечения (локальное): {expires_datetime.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("\n" + "="*60)
        
        # Также выводим полный ответ в JSON формате
        token_data = get_gigachat_token_dict()
        # Преобразуем datetime в строку для JSON
        json_data = token_data.copy()
        if json_data.get("expires_at_datetime"):
            json_data["expires_at_datetime"] = json_data["expires_at_datetime"].isoformat()
        
        print("\nПолный ответ (JSON):")
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Ошибка: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
