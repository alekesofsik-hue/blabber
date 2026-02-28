"""
Config repository — CRUD operations for config table.
"""

from __future__ import annotations

from typing import Any

from database import get_connection


def _row_to_dict(row) -> dict[str, Any] | None:
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return {k: row[k] for k in row.keys()} if hasattr(row, "keys") else dict(row)


def get(key: str) -> dict[str, Any] | None:
    """Get single config entry by key."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM config WHERE key = ?", (key,)).fetchone()
        return _row_to_dict(row) if row else None


def get_all(category: str | None = None) -> list[dict[str, Any]]:
    """Get all config entries, optionally filtered by category."""
    with get_connection() as conn:
        if category:
            rows = conn.execute(
                "SELECT * FROM config WHERE category = ? ORDER BY key",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM config ORDER BY category, key").fetchall()
        return [_row_to_dict(r) for r in rows]


def upsert(
    key: str,
    value: str,
    value_type: str = "str",
    category: str = "general",
    description: str | None = None,
    is_secret: bool = False,
    updated_by: int | None = None,
) -> None:
    """
    Insert or update config entry.

    Args:
        key: Config key (unique)
        value: String representation of value
        value_type: str, int, float, bool, json
        category: Category for grouping
        description: Optional description
        is_secret: If True, mask when displaying
        updated_by: Telegram ID of admin who made the change
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO config (key, value, value_type, category, description, is_secret, updated_at, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                value_type = excluded.value_type,
                category = excluded.category,
                description = excluded.description,
                is_secret = excluded.is_secret,
                updated_at = datetime('now'),
                updated_by = excluded.updated_by
            """,
            (key, str(value), value_type, category, description, 1 if is_secret else 0, updated_by),
        )


def delete(key: str) -> bool:
    """Delete config entry. Returns True if deleted."""
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM config WHERE key = ?", (key,))
        return cur.rowcount > 0
