"""
Middleware — access control and user context for Blabber bot.
"""

from middleware.auth import require_role, require_role_callback, with_user_check

__all__ = ["require_role", "require_role_callback", "with_user_check"]
