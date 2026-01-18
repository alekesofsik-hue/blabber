"""
Простое хранилище выбора модели пользователями.
Хранит выбор модели для каждого пользователя в памяти.
"""

from __future__ import annotations

from typing import Dict

# Словарь для хранения выбора модели: {user_id: 'gigachat', 'openrouter', 'yandexgpt' или 'ollama'}
user_models: Dict[int, str] = {}

# Доступные модели
AVAILABLE_MODELS = {
    'gigachat': 'GigaChat',
    'openrouter': 'OpenRouter (DeepSeek)',
    'yandexgpt': 'Yandex GPT',
    'ollama': 'Ollama (local)'
}

DEFAULT_MODEL = 'openrouter'


def get_user_model(user_id: int) -> str:
    """
    Получить выбранную модель для пользователя.
    
    Args:
        user_id: ID пользователя Telegram
        
    Returns:
        Имя модели ('gigachat', 'openrouter', 'yandexgpt' или 'ollama')
    """
    return user_models.get(user_id, DEFAULT_MODEL)


def set_user_model(user_id: int, model: str) -> bool:
    """
    Установить модель для пользователя.
    
    Args:
        user_id: ID пользователя Telegram
        model: Имя модели ('gigachat', 'openrouter', 'yandexgpt' или 'ollama')
        
    Returns:
        True если модель установлена, False если модель не поддерживается
    """
    if model in AVAILABLE_MODELS:
        user_models[user_id] = model
        return True
    return False


def get_available_models() -> Dict[str, str]:
    """
    Получить список доступных моделей.
    
    Returns:
        Словарь с доступными моделями
    """
    return AVAILABLE_MODELS.copy()

