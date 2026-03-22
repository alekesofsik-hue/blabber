"""
Тексты Telegram-бота, редактируемые в одном месте.

- Встроенные шаблоны по умолчанию — в `bot_texts.defaults`.
- Переопределение из админки (БД `config`): ключи `welcome_message`, `help_message`.
  Пустая строка или отсутствие ключа = использовать встроенный шаблон из кода.

См. также: `/admin` → Конфигурация → messages, команды `/setconfig`.
"""

from bot_texts.defaults import (
    HELP_MESSAGE_HTML,
    START_MESSAGE_HTML_TEMPLATE,
    resolve_help_message,
    resolve_start_message,
)

__all__ = [
    "HELP_MESSAGE_HTML",
    "START_MESSAGE_HTML_TEMPLATE",
    "resolve_help_message",
    "resolve_start_message",
]
