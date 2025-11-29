# LLM Providers - Универсальные модули для работы с LLM API

Эта папка содержит три независимых модуля для работы с различными языковыми моделями:

- **openrouter.py** - модуль для OpenRouter API (DeepSeek и другие модели)
- **gigachat.py** - модуль для GigaChat API
- **yandexgpt.py** - модуль для Yandex GPT API

## Особенности

✅ **Единый интерфейс** - все модули имеют функцию `get_response()` с одинаковой сигнатурой  
✅ **Самодостаточность** - каждый модуль содержит всю необходимую логику  
✅ **Гибкость** - дополнительные параметры передаются через `**kwargs`  
✅ **Переиспользуемость** - модули можно копировать в другие проекты  

## Быстрый старт

### OpenRouter (DeepSeek)

```python
from llm_providers.openrouter import get_response

response = get_response(
    message="Расскажи про Python",
    system_message="Ты опытный программист",
    model="deepseek/deepseek-chat"
)
```

### GigaChat

```python
from llm_providers.gigachat import get_response

response = get_response(
    message="Привет!",
    system_message="Ты дружелюбный помощник"
)
```

### Yandex GPT

```python
from llm_providers.yandexgpt import get_response

response = get_response(
    message="Что такое машинное обучение?",
    system_message="Ты эксперт по AI",
    temperature=0.7
)
```

## Переменные окружения

Каждый модуль может использовать переменные окружения из `.env` файла:

- **OpenRouter**: `PROXY_API_KEY`
- **GigaChat**: `GIGACHAT_CREDENTIALS`, `GIGACHAT_VERIFY_SSL`
- **Yandex GPT**: `YANDEX_API_KEY`, `YANDEX_FOLDER_ID`, `YANDEX_MODEL`

Также все параметры можно передавать напрямую через `**kwargs`.

## Использование в других проектах

1. Скопируйте папку `llm_providers` в ваш проект
2. Убедитесь, что установлены необходимые зависимости (см. `requirements.txt`)
3. Импортируйте нужный модуль и используйте функцию `get_response()`

## Зависимости

- `openai` - для OpenRouter
- `httpx` или `requests` - для HTTP запросов
- `yandex-cloud-ml-sdk` - для Yandex GPT
- `python-dotenv` - для загрузки переменных окружения
- `get_token_gch.py` - для GigaChat (должен быть доступен в проекте)

Подробную документацию по каждому модулю см. в docstring файлов.

