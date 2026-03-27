"""
Handlers — message and callback handlers for Blabber bot.
"""

from handlers.admin_commands import register_admin_handlers
from handlers.agent_commands import register_agent_handlers
from handlers.history_day_commands import register_history_day_handlers
from handlers.knowledge_commands import register_knowledge_handlers
from handlers.persona_commands import register_persona_handlers
from handlers.profile_commands import register_profile_handlers
from handlers.quote_commands import register_quote_handlers
from handlers.report_commands import register_report_handlers

__all__ = [
    "register_admin_handlers",
    "register_profile_handlers",
    "register_knowledge_handlers",
    "register_agent_handlers",
    "register_history_day_handlers",
    "register_persona_handlers",
    "register_quote_handlers",
    "register_report_handlers",
]
