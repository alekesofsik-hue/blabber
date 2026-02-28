"""
Универсальный модуль для работы с Yandex GPT API.

Использование:
    from llm_providers.yandexgpt import get_response
    
    response = get_response(
        message="Привет!",
        system_message="Ты помощник",
        api_key="your_key",
        folder_id="your_folder_id"
    )
"""

import os
from typing import Any, Optional
from dotenv import load_dotenv

try:
    from yandex_cloud_ml_sdk import YCloudML
    YANDEX_SDK_AVAILABLE = True
except ImportError:
    YANDEX_SDK_AVAILABLE = False

load_dotenv()


def get_response(
    message: str,
    system_message: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Получить ответ от Yandex GPT API.
    
    Args:
        message: Сообщение пользователя
        system_message: Системное сообщение для настройки поведения модели
        **kwargs: Дополнительные параметры:
            - api_key: API ключ (если не указан, берётся из YANDEX_API_KEY)
            - folder_id: ID каталога (если не указан, берётся из YANDEX_FOLDER_ID)
            - model: Название модели (по умолчанию: yandexgpt)
            - temperature: Температура генерации (по умолчанию: 0.8)
            - history: список {"role", "content"} для контекста диалога
    
    Returns:
        Ответ от модели в виде строки
    
    Raises:
        ValueError: Если api_key или folder_id не указаны
        Exception: При ошибке обращения к API
    """
    if not YANDEX_SDK_AVAILABLE:
        raise Exception(
            "Библиотека yandex-cloud-ml-sdk не установлена. "
            "Установите её: pip install yandex-cloud-ml-sdk"
        )
    
    # Получаем параметры из kwargs или переменных окружения
    api_key = kwargs.get('api_key') or os.getenv("YANDEX_API_KEY")
    folder_id = kwargs.get('folder_id') or os.getenv("YANDEX_FOLDER_ID")
    model_name = kwargs.get('model') or os.getenv("YANDEX_MODEL", "yandexgpt")
    temperature = kwargs.get('temperature', 0.8)
    
    if not api_key:
        raise ValueError(
            "YANDEX_API_KEY не установлен. "
            "Укажите api_key в kwargs или установите YANDEX_API_KEY в .env"
        )
    if not folder_id:
        raise ValueError(
            "YANDEX_FOLDER_ID не установлен. "
            "Укажите folder_id в kwargs или установите YANDEX_FOLDER_ID в .env"
        )
    
    history: list = kwargs.get("history") or []

    try:
        # Создаём SDK клиент
        sdk = YCloudML(
            folder_id=folder_id,
            auth=api_key,
        )

        # Получаем модель completions
        model = sdk.models.completions(model_name)

        # Формируем сообщения для модели
        # Yandex GPT uses "text" instead of "content"
        messages = []
        if system_message:
            messages.append({"role": "system", "text": system_message})
        for h in history:
            messages.append({"role": h["role"], "text": h["content"]})
        messages.append({"role": "user", "text": message})
        
        # Запускаем асинхронный запрос и ждём результат
        operation = model.configure(temperature=temperature).run_deferred(messages)
        result = operation.wait()
        
        # Извлекаем ответ из структуры GPTModelResult
        if result and hasattr(result, 'alternatives') and len(result.alternatives) > 0:
            alternative = result.alternatives[0]
            if hasattr(alternative, 'text') and alternative.text:
                return alternative.text
        
        raise ValueError("Пустой ответ от Yandex GPT API")
        
    except Exception as e:
        error_msg = str(e)
        # Обработка ошибок доступа
        if 'PERMISSION_DENIED' in error_msg or 'Permission denied' in error_msg or 'grpc_status:7' in error_msg:
            raise Exception(
                f"❌ Ошибка доступа к Yandex GPT API: Permission denied\n\n"
                f"Возможные причины:\n"
                f"1. API ключ неверный или не имеет необходимых прав\n"
                f"2. Сервисный аккаунт не имеет роли для работы с Yandex GPT\n"
                f"3. Yandex GPT API не активирован в каталоге {folder_id}\n"
                f"4. Неправильный идентификатор каталога\n\n"
                f"Что нужно сделать:\n"
                f"• Проверьте корректность API ключа\n"
                f"• Убедитесь, что YANDEX_FOLDER_ID правильный\n"
                f"• Убедитесь, что сервисный аккаунт имеет роль `ai.languageModels.user` или `ai.user`\n"
                f"• Проверьте, что Yandex GPT активирован в консоли Yandex Cloud\n\n"
                f"Исходная ошибка: {error_msg}"
            )
        # Обработка других ошибок
        raise Exception(f"Ошибка при обращении к Yandex GPT API: {error_msg}") from e

