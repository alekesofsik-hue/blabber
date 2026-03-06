"""
Persona service — manages per-user "role" personas loaded from prompts.json.

Each role has a name, description and system_prompt.
The selected role's system_prompt is appended to the bot's base persona
so the "балабол" personality is preserved while the role adds focus.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from database import get_connection
from repositories.user_repo import get_by_telegram_id

logger = logging.getLogger("blabber")

_PROMPTS_FILE = Path(__file__).resolve().parent.parent / "prompts.json"

# ── Load prompts.json once at import time ─────────────────────────────────────

def _load_prompts() -> dict:
    try:
        with open(_PROMPTS_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.error("persona_prompts_load_failed", extra={"error": str(exc)})
        return {"default_role": "assistant", "roles": {}}


_PROMPTS: dict = _load_prompts()
_ROLES: dict[str, dict] = _PROMPTS.get("roles", {})
_DEFAULT_ROLE: str = _PROMPTS.get("default_role", "assistant")


# ── Public read-only API ──────────────────────────────────────────────────────

def get_roles() -> dict[str, dict]:
    """Return all available roles keyed by their slug."""
    return _ROLES


def get_role_info(role_key: str) -> dict | None:
    """Return role dict {name, description, system_prompt} or None if unknown."""
    return _ROLES.get(role_key)


def get_default_role() -> str:
    return _DEFAULT_ROLE


# ── Per-user role persistence ─────────────────────────────────────────────────

def get_user_role(telegram_id: int) -> str:
    """Return the role key currently set for user. Falls back to default."""
    user = get_by_telegram_id(telegram_id)
    if not user:
        return _DEFAULT_ROLE
    role = user.get("current_role") or _DEFAULT_ROLE
    # Guard against stale keys that no longer exist in prompts.json
    return role if role in _ROLES else _DEFAULT_ROLE


def set_user_role(telegram_id: int, role_key: str) -> bool:
    """
    Persist chosen role key for user.

    Returns True on success, False if role_key is unknown or user not found.
    """
    if role_key not in _ROLES:
        return False
    user = get_by_telegram_id(telegram_id)
    if not user:
        return False
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET current_role = ? WHERE telegram_id = ?",
                (role_key, telegram_id),
            )
        return True
    except Exception as exc:
        logger.warning("persona_set_role_failed", extra={"error": str(exc)})
        return False


# ── System prompt builder ─────────────────────────────────────────────────────

def build_persona_addon(telegram_id: int) -> str | None:
    """
    Return the role's system_prompt to append to the base system message,
    or None if the user is on the default 'assistant' role and it adds nothing
    meaningful on top of the base балабол persona.

    We always return the prompt so the caller can decide.
    """
    role_key = get_user_role(telegram_id)
    role = _ROLES.get(role_key)
    if not role:
        return None
    return role.get("system_prompt") or None
