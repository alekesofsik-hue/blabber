"""
Универсальные модули для работы с различными LLM API.

Каждый модуль предоставляет функцию get_response() для получения ответов от моделей.
Модули можно использовать независимо в других проектах.

Пример использования:
    from llm_providers.openrouter import get_response as openrouter_get_response
    from llm_providers.gigachat import get_response as gigachat_get_response
    from llm_providers.yandexgpt import get_response as yandexgpt_get_response
    
    response = openrouter_get_response("Привет!", system_message="Ты помощник")
"""

from .openrouter import get_response as openrouter_get_response
from .gigachat import get_response as gigachat_get_response
from .yandexgpt import get_response as yandexgpt_get_response

__all__ = [
    'openrouter_get_response',
    'gigachat_get_response',
    'yandexgpt_get_response',
]

