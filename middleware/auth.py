"""
Auth middleware — RBAC decorators and user check.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING, Callable

from services.user_service import get_or_create, is_banned

if TYPE_CHECKING:
    pass

logger = logging.getLogger("blabber")

MSG_INSUFFICIENT_RIGHTS = "⛔ Недостаточно прав."
MSG_BANNED = "⛔ Ваш доступ заблокирован."


def require_role(bot, min_weight: int = 100):
    """
    Decorator for message handlers — requires user role with weight >= min_weight.

    Usage:
        @bot.message_handler(commands=['admin'])
        @require_role(bot, min_weight=100)
        def handle_admin(message):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            user = get_or_create(message.from_user)
            if user is None:
                bot.reply_to(message, MSG_INSUFFICIENT_RIGHTS)
                logger.warning(
                    "auth_failed_no_user",
                    extra={
                        "event": "auth_failed_no_user",
                        "telegram_id": message.from_user.id,
                        "command": getattr(message, "text", ""),
                        "required_weight": min_weight,
                    },
                )
                return

            if is_banned(message.from_user.id):
                bot.reply_to(message, MSG_BANNED)
                logger.warning(
                    "blocked_admin_tried",
                    extra={
                        "event": "blocked_admin_tried",
                        "telegram_id": message.from_user.id,
                        "command": getattr(message, "text", ""),
                    },
                )
                return

            role_weight = user.get("role_weight") or 0
            if role_weight < min_weight:
                bot.reply_to(message, MSG_INSUFFICIENT_RIGHTS)
                logger.warning(
                    "unauthorized_access",
                    extra={
                        "event": "unauthorized_access",
                        "telegram_id": message.from_user.id,
                        "user_role_weight": role_weight,
                        "required_weight": min_weight,
                        "command": getattr(message, "text", ""),
                    },
                )
                return

            return func(message, *args, **kwargs)

        return wrapper

    return decorator


def require_role_callback(bot, min_weight: int = 100):
    """
    Decorator for callback_query handlers — requires user role with weight >= min_weight.

    Usage:
        @bot.callback_query_handler(func=lambda c: c.data.startswith('admin_'))
        @require_role_callback(bot, min_weight=100)
        def handle_admin_callback(call):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(call, *args, **kwargs):
            user = get_or_create(call.from_user)
            if user is None:
                bot.answer_callback_query(call.id, MSG_INSUFFICIENT_RIGHTS, show_alert=True)
                logger.warning(
                    "auth_failed_no_user_callback",
                    extra={
                        "event": "auth_failed_no_user_callback",
                        "telegram_id": call.from_user.id,
                        "callback_data": getattr(call, "data", ""),
                        "required_weight": min_weight,
                    },
                )
                return

            if is_banned(call.from_user.id):
                bot.answer_callback_query(call.id, MSG_BANNED, show_alert=True)
                return

            role_weight = user.get("role_weight") or 0
            if role_weight < min_weight:
                bot.answer_callback_query(call.id, MSG_INSUFFICIENT_RIGHTS, show_alert=True)
                logger.warning(
                    "unauthorized_access_callback",
                    extra={
                        "event": "unauthorized_access_callback",
                        "telegram_id": call.from_user.id,
                        "user_role_weight": role_weight,
                        "required_weight": min_weight,
                        "callback_data": getattr(call, "data", ""),
                    },
                )
                return

            return func(call, *args, **kwargs)

        return wrapper

    return decorator


def with_user_check(bot):
    """
    Decorator that ensures user is registered and not banned before handler runs.

    Calls get_or_create, checks is_active. If banned, sends message and returns.
    Attaches user dict to message._user for handlers that need it.

    Usage:
        @bot.message_handler(commands=['start'])
        @with_user_check(bot)
        def handle_start(message):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            user = get_or_create(message.from_user)
            if user is None:
                bot.reply_to(message, "⛔ Произошла ошибка. Попробуйте позже.")
                logger.error(
                    "user_registration_failed",
                    extra={"event": "user_registration_failed", "telegram_id": message.from_user.id},
                )
                return

            if is_banned(message.from_user.id):
                bot.reply_to(message, MSG_BANNED)
                logger.warning(
                    "blocked_user_tried",
                    extra={
                        "event": "blocked_user_tried",
                        "telegram_id": message.from_user.id,
                        "command": getattr(message, "text", ""),
                    },
                )
                return

            message._user = user
            return func(message, *args, **kwargs)

        return wrapper

    return decorator
