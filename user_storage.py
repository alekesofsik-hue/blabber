"""
Простое хранилище настроек пользователей.

Хранит в памяти:
- выбор LLM-модели для каждого пользователя
- включение/выключение голосовых ответов (TTS)
- выбранный голос TTS
- включение/выключение базы знаний (RAG)
- включение/выключение agent-режима ("Балабол-новостник")
"""

from __future__ import annotations

# ────────────────────── LLM-модели ──────────────────────

# Словарь для хранения выбора модели: {user_id: model_key}
user_models: dict[int, str] = {}

# Доступные модели
AVAILABLE_MODELS = {
    'gigachat': 'GigaChat',
    'openrouter': 'OpenRouter (DeepSeek)',
    'reasoning': 'DeepSeek R1 (рассуждающая)',
    'openai': 'OpenAI (GPT-4o)',
    'yandexgpt': 'Yandex GPT',
    'ollama': 'Ollama (local)',
}

DEFAULT_MODEL = 'openrouter'


def get_user_model(user_id: int) -> str:
    """
    Получить выбранную модель для пользователя.

    Args:
        user_id: ID пользователя Telegram

    Returns:
        Имя модели ('gigachat', 'openrouter', 'reasoning', 'yandexgpt' или 'ollama')
    """
    return user_models.get(user_id, DEFAULT_MODEL)


def set_user_model(user_id: int, model: str) -> bool:
    """
    Установить модель для пользователя.

    Args:
        user_id: ID пользователя Telegram
        model: Имя модели ('gigachat', 'openrouter', 'reasoning', 'yandexgpt' или 'ollama')

    Returns:
        True если модель установлена, False если модель не поддерживается
    """
    if model in AVAILABLE_MODELS:
        user_models[user_id] = model
        return True
    return False


def get_available_models() -> dict[str, str]:
    """
    Получить список доступных моделей.

    Returns:
        Словарь с доступными моделями
    """
    return AVAILABLE_MODELS.copy()


# ────────────────────── Голосовые ответы (TTS) ──────────────────────

# {user_id: True/False}
user_voice_enabled: dict[int, bool] = {}

# {user_id: voice_key}  — 'alena', 'filipp', 'ermil', 'jane', 'omazh', 'zahar', 'marina', ...
user_voice_choice: dict[int, str] = {}

DEFAULT_VOICE_ENABLED = False
DEFAULT_VOICE = "alena"


def is_voice_enabled(user_id: int) -> bool:
    """Проверить, включена ли озвучка у пользователя."""
    return user_voice_enabled.get(user_id, DEFAULT_VOICE_ENABLED)


def set_voice_enabled(user_id: int, enabled: bool) -> None:
    """Включить или выключить озвучку для пользователя."""
    user_voice_enabled[user_id] = enabled


def get_user_voice(user_id: int) -> str:
    """Получить выбранный голос пользователя."""
    from tts import get_available_voices

    stored = user_voice_choice.get(user_id, DEFAULT_VOICE)
    if stored in get_available_voices():
        return stored
    return DEFAULT_VOICE  # fallback при смене провайдера TTS


def set_user_voice(user_id: int, voice_key: str) -> bool:
    """
    Установить голос для пользователя.

    Returns:
        True если голос установлен, False если голос не поддерживается.
    """
    from tts import get_available_voices

    if voice_key in get_available_voices():
        user_voice_choice[user_id] = voice_key
        return True
    return False


# ────────────────────── База знаний (RAG) ──────────────────────

# {user_id: True/False}  — off by default until user uploads a document
_user_kb_enabled: dict[int, bool] = {}

DEFAULT_KB_ENABLED = False


def is_kb_enabled(user_id: int) -> bool:
    """Проверить, включена ли база знаний для пользователя."""
    return _user_kb_enabled.get(user_id, DEFAULT_KB_ENABLED)


def set_kb_enabled(user_id: int, enabled: bool) -> None:
    """Включить или выключить базу знаний для пользователя."""
    _user_kb_enabled[user_id] = enabled


# ────────────────────── Agent-режим ("Балабол-новостник") ──────────────────────

# {user_id: True/False}  — off by default
_user_agent_enabled: dict[int, bool] = {}

DEFAULT_AGENT_ENABLED = False


def is_agent_enabled(user_id: int) -> bool:
    """Проверить, включён ли agent-режим для пользователя."""
    return _user_agent_enabled.get(user_id, DEFAULT_AGENT_ENABLED)


def set_agent_enabled(user_id: int, enabled: bool) -> None:
    """Включить или выключить agent-режим для пользователя."""
    _user_agent_enabled[user_id] = enabled

