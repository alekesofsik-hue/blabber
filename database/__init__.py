"""
Database package for Blabber bot.

Provides SQLite-based persistent storage with automatic migration support.
"""

from database.engine import get_connection, init_db

__all__ = ["init_db", "get_connection"]
