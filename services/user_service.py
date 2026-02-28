"""
User service — business logic for user management.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from repositories.user_repo import (
    get_by_telegram_id,
    create,
    update_role,
    set_active,
    list_users,
    count_users,
)
from database import get_connection
from services.config_registry import get_setting

logger = logging.getLogger("blabber")

# Bootstrap: Telegram IDs that get auto-promoted to admin
_INITIAL_ADMIN_IDS: frozenset[int] | None = None


def get_admin_telegram_ids() -> frozenset[int]:
    """Load ADMIN_TELEGRAM_IDS from env (cached)."""
    global _INITIAL_ADMIN_IDS
    if _INITIAL_ADMIN_IDS is None:
        raw = os.environ.get("ADMIN_TELEGRAM_IDS", "")
        ids = frozenset(
            int(x.strip()) for x in raw.split(",") if x.strip()
        )
        _INITIAL_ADMIN_IDS = ids
    return _INITIAL_ADMIN_IDS


def _get_role_id_by_name(name: str) -> int | None:
    """Get role id by name."""
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM roles WHERE name = ?", (name,)).fetchone()
        return row["id"] if row else None


def get_or_create(telegram_user) -> dict[str, Any] | None:
    """
    Get existing user or create new one (auto-registration).

    Applies bootstrap: if telegram_id is in ADMIN_TELEGRAM_IDS and role < admin,
    promotes to admin.

    Args:
        telegram_user: Telegram User object (message.from_user)
                       with .id, .username, .first_name

    Returns:
        User dict with role_name and role_weight, or None on error
    """
    telegram_id = telegram_user.id
    username = getattr(telegram_user, "username", None)
    first_name = getattr(telegram_user, "first_name", None)

    user = get_by_telegram_id(telegram_id)

    if user:
        # Bootstrap: promote to admin if in whitelist and not yet admin
        admin_ids = get_admin_telegram_ids()
        if telegram_id in admin_ids and user.get("role_weight", 0) < 100:
            role_id = _get_role_id_by_name("admin")
            if role_id:
                update_role(telegram_id, role_id)
                logger.info(
                    "admin_bootstrap",
                    extra={
                        "event": "admin_bootstrap",
                        "telegram_id": telegram_id,
                        "username": username,
                    },
                )
                user = get_by_telegram_id(telegram_id)
        return user

    # Create new user
    role_id = _get_role_id_by_name("user")
    if role_id is None:
        logger.error("roles_table_empty", extra={"event": "roles_table_empty"})
        return None

    # Bootstrap: if in admin whitelist, create as admin
    if telegram_id in get_admin_telegram_ids():
        admin_role_id = _get_role_id_by_name("admin")
        if admin_role_id:
            role_id = admin_role_id
            logger.info(
                "admin_bootstrap_new",
                extra={"event": "admin_bootstrap_new", "telegram_id": telegram_id},
            )

    preferred_model = get_setting("default_model", "openrouter")
    user = create(telegram_id, username, first_name, role_id, preferred_model=preferred_model)
    logger.info(
        "user_registered",
        extra={
            "event": "user_registered",
            "telegram_id": telegram_id,
            "username": username,
            "role": user.get("role_name"),
        },
    )
    return user


def set_role(telegram_id: int, role_name: str) -> bool:
    """Set user role by name (user, moderator, admin)."""
    role_id = _get_role_id_by_name(role_name)
    if role_id is None:
        return False
    return update_role(telegram_id, role_id)


def ban(telegram_id: int) -> bool:
    """Ban user (is_active = False)."""
    return set_active(telegram_id, False)


def unban(telegram_id: int) -> bool:
    """Unban user (is_active = True)."""
    return set_active(telegram_id, True)


def get_user_info(telegram_id: int) -> dict[str, Any] | None:
    """Get full user info."""
    return get_by_telegram_id(telegram_id)


def is_banned(telegram_id: int) -> bool:
    """Check if user is banned (is_active = False)."""
    user = get_by_telegram_id(telegram_id)
    if user is None:
        return False  # Not registered = not banned
    return not bool(user.get("is_active", 1))


def list_users_paginated(
    offset: int = 0, limit: int = 10, role_filter: str | None = None
) -> list[dict[str, Any]]:
    """List users with pagination."""
    return list_users(offset, limit, role_filter)


def count_users_total(role_filter: str | None = None) -> int:
    """Count users."""
    return count_users(role_filter)
