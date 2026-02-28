"""
Repositories layer — data access for Blabber bot.
"""

from repositories.user_repo import (
    get_by_telegram_id,
    create,
    update_role,
    set_active,
    update_preferences,
    list_users,
    count_users,
)

__all__ = [
    "get_by_telegram_id",
    "create",
    "update_role",
    "set_active",
    "update_preferences",
    "list_users",
    "count_users",
]
