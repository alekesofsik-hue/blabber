"""
Auto memory repository — persistence for suggestion payloads and per-user flags.
"""

from __future__ import annotations

from database import get_connection


def get_user_settings(telegram_id: int) -> dict | None:
    """
    Return per-user auto-memory settings:
      {"user_db_id": int, "enabled": bool, "last_suggested_at": str|None}
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, auto_memory_enabled, auto_memory_last_suggested_at
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "user_db_id": row["id"],
            "enabled": bool(row["auto_memory_enabled"]),
            "last_suggested_at": row["auto_memory_last_suggested_at"],
        }


def set_enabled(telegram_id: int, enabled: bool) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE users SET auto_memory_enabled = ?, updated_at = datetime('now') WHERE telegram_id = ?",
            (1 if enabled else 0, telegram_id),
        )
        return cur.rowcount > 0


def touch_last_suggested(user_db_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET auto_memory_last_suggested_at = datetime('now') WHERE id = ?",
            (user_db_id,),
        )


def create_suggestion(suggestion_id: str, user_db_id: int, items_json: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO memory_suggestions (id, user_id, items_json) VALUES (?, ?, ?)",
            (suggestion_id, user_db_id, items_json),
        )


def get_suggestion(suggestion_id: str, user_db_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, items_json, status, created_at
            FROM memory_suggestions
            WHERE id = ? AND user_id = ?
            """,
            (suggestion_id, user_db_id),
        ).fetchone()
        return dict(row) if row else None


def update_items_json(suggestion_id: str, user_db_id: int, items_json: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE memory_suggestions SET items_json = ? WHERE id = ? AND user_id = ?",
            (items_json, suggestion_id, user_db_id),
        )


def set_status(suggestion_id: str, user_db_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE memory_suggestions SET status = ? WHERE id = ? AND user_id = ?",
            (status, suggestion_id, user_db_id),
        )

