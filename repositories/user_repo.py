"""
User repository — CRUD operations for users table.
"""

from __future__ import annotations

from typing import Any

from database import get_connection


def _row_to_dict(row) -> dict[str, Any] | None:
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return {k: row[k] for k in row.keys()} if hasattr(row, "keys") else dict(row)


def _get_role_id_by_name(conn, name: str) -> int | None:
    """Get role id by name."""
    row = conn.execute("SELECT id FROM roles WHERE name = ?", (name,)).fetchone()
    return row["id"] if row else None


def get_by_telegram_id(telegram_id: int) -> dict[str, Any] | None:
    """
    Get user by Telegram ID with joined role info.

    Returns:
        User dict with role_name and role_weight, or None if not found.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.*, r.name AS role_name, r.weight AS role_weight
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
        return _row_to_dict(row) if row else None


def create(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    role_id: int,
    preferred_model: str | None = None,
) -> dict[str, Any]:
    """
    Create a new user.

    Args:
        preferred_model: Optional default model (from config). If None, uses table default.
    """
    with get_connection() as conn:
        if preferred_model:
            conn.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, role_id, preferred_model,
                                   limits_reset_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', '+24 hours'))
                """,
                (telegram_id, username or None, first_name or None, role_id, preferred_model),
            )
        else:
            conn.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, role_id,
                                   limits_reset_at)
                VALUES (?, ?, ?, ?, datetime('now', '+24 hours'))
                """,
                (telegram_id, username or None, first_name or None, role_id),
            )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        row = conn.execute(
            """
            SELECT u.*, r.name AS role_name, r.weight AS role_weight
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = ?
            """,
            (row_id,),
        ).fetchone()
        return _row_to_dict(row)


def update_role(telegram_id: int, role_id: int) -> bool:
    """Update user role. Returns True if updated."""
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE users SET role_id = ?, updated_at = datetime('now') WHERE telegram_id = ?",
            (role_id, telegram_id),
        )
        return cur.rowcount > 0


def set_active(telegram_id: int, is_active: bool) -> bool:
    """Set user active status (ban/unban). Returns True if updated."""
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE users SET is_active = ?, updated_at = datetime('now') WHERE telegram_id = ?",
            (1 if is_active else 0, telegram_id),
        )
        return cur.rowcount > 0


def update_preferences(telegram_id: int, **kwargs: Any) -> bool:
    """
    Update user preferences (preferred_model, voice_enabled, voice_choice).

    Only updates provided keys.
    """
    allowed = {"preferred_model", "voice_enabled", "voice_choice"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False

    # Normalize booleans for SQLite
    if "voice_enabled" in updates:
        updates["voice_enabled"] = 1 if updates["voice_enabled"] else 0

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [telegram_id]

    with get_connection() as conn:
        cur = conn.execute(
            f"UPDATE users SET {set_clause}, updated_at = datetime('now') WHERE telegram_id = ?",
            values,
        )
        return cur.rowcount > 0


def list_users(offset: int = 0, limit: int = 10, role_filter: str | None = None) -> list[dict[str, Any]]:
    """
    List users with optional role filter.

    Args:
        offset: Pagination offset
        limit: Page size
        role_filter: Optional role name filter (user, moderator, admin)
    """
    with get_connection() as conn:
        if role_filter:
            rows = conn.execute(
                """
                SELECT u.*, r.name AS role_name, r.weight AS role_weight
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE r.name = ?
                ORDER BY u.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (role_filter, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT u.*, r.name AS role_name, r.weight AS role_weight
                FROM users u
                JOIN roles r ON u.role_id = r.id
                ORDER BY u.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [_row_to_dict(r) for r in rows]


def reset_limits(telegram_id: int) -> bool:
    """Reset daily counters and set limits_reset_at to now+24h."""
    from datetime import datetime, timedelta

    next_reset = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE users
            SET tokens_used_today = 0, requests_today = 0, limits_reset_at = ?, updated_at = datetime('now')
            WHERE telegram_id = ?
            """,
            (next_reset, telegram_id),
        )
        return cur.rowcount > 0


def update_limits(
    telegram_id: int,
    daily_token_limit: int | None = None,
    daily_request_limit: int | None = None,
) -> bool:
    """Update user limits. Returns True if updated."""
    updates = []
    values = []
    if daily_token_limit is not None:
        updates.append("daily_token_limit = ?")
        values.append(daily_token_limit)
    if daily_request_limit is not None:
        updates.append("daily_request_limit = ?")
        values.append(daily_request_limit)
    if not updates:
        return False
    values.append(telegram_id)
    with get_connection() as conn:
        cur = conn.execute(
            f"UPDATE users SET {', '.join(updates)}, updated_at = datetime('now') WHERE telegram_id = ?",
            values,
        )
        return cur.rowcount > 0


def search_users(q: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search users by telegram_id (exact) or username (LIKE)."""
    with get_connection() as conn:
        query = q.strip()
        if not query:
            return []
        # Try telegram_id first (exact)
        try:
            tid = int(query)
            rows = conn.execute(
                """
                SELECT u.*, r.name AS role_name, r.weight AS role_weight
                FROM users u JOIN roles r ON u.role_id = r.id
                WHERE u.telegram_id = ?
                """,
                (tid,),
            ).fetchall()
            return [_row_to_dict(r) for r in rows]
        except ValueError:
            pass
        # Search by username
        rows = conn.execute(
            """
            SELECT u.*, r.name AS role_name, r.weight AS role_weight
            FROM users u JOIN roles r ON u.role_id = r.id
            WHERE u.username LIKE ? OR u.first_name LIKE ?
            ORDER BY u.created_at DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def count_users(role_filter: str | None = None) -> int:
    """Count users, optionally filtered by role."""
    with get_connection() as conn:
        if role_filter:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM users u JOIN roles r ON u.role_id = r.id WHERE r.name = ?",
                (role_filter,),
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        return row["cnt"]
