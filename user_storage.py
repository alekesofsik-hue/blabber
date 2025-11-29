"""
Простое хранилище выбора модели пользователями.
Хранит выбор модели для каждого пользователя в памяти.
"""

# Словарь для хранения выбора модели: {user_id: 'gigachat', 'openrouter' или 'yandexgpt'}
user_models = {}

# Доступные модели
AVAILABLE_MODELS = {
    'gigachat': 'GigaChat',
    'openrouter': 'OpenRouter (DeepSeek)',
    'yandexgpt': 'Yandex GPT'
}

DEFAULT_MODEL = 'openrouter'


def get_user_model(user_id: int) -> str:
    """
    Получить выбранную модель для пользователя.
    
    Args:
        user_id: ID пользователя Telegram
        
    Returns:
        Имя модели ('gigachat', 'openrouter' или 'yandexgpt')
    """
    return user_models.get(user_id, DEFAULT_MODEL)


def set_user_model(user_id: int, model: str) -> bool:
    """
    Установить модель для пользователя.
    
    Args:
        user_id: ID пользователя Telegram
        model: Имя модели ('gigachat', 'openrouter' или 'yandexgpt')
        
    Returns:
        True если модель установлена, False если модель не поддерживается
    """
    if model in AVAILABLE_MODELS:
        user_models[user_id] = model
        return True
    return False


def get_available_models() -> dict:
    """
    Получить список доступных моделей.
    
    Returns:
        Словарь с доступными моделями
    """
    return AVAILABLE_MODELS.copy()

