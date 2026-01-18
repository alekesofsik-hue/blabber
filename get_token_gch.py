"""
Compatibility wrapper for GigaChat token utilities.

The actual implementation lives in `llm_providers.gigachat_token` so it can be reused
without relying on project root imports.

Usage as module:
    from get_token_gch import get_gigachat_token, get_gigachat_token_dict, get_gigachat_token_info

Usage as script:
    python get_token_gch.py
"""

import json
import sys

from llm_providers.gigachat_token import (
    get_gigachat_token,
    get_gigachat_token_dict,
    get_gigachat_token_info,
)


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
