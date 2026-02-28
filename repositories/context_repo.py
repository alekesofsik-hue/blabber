"""
Context repository — CRUD for context_messages, context_summary, and context_mode.

All operations accept user_db_id (users.id, the internal integer PK),
except set_context_mode / get_context_mode which accept telegram_id
(more convenient at the call site).
"""

from __future__ import annotations

from typing import Any

from database import get_connection


# ── Messages ──────────────────────────────────────────────────────────────────

def get_messages(user_db_id: int) -> list[dict[str, Any]]:
    """Return all messages for user, ordered oldest-first."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM context_messages
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_db_id,),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows]


def add_message(user_db_id: int, role: str, content: str) -> None:
    """Insert a single message (role: 'user' or 'assistant')."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO context_messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_db_id, role, content),
        )


def delete_messages(user_db_id: int) -> None:
    """Delete all messages for user."""
    with get_connection() as conn:
        conn.execute("DELETE FROM context_messages WHERE user_id = ?", (user_db_id,))


def count_messages(user_db_id: int) -> int:
    """Count messages for user."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM context_messages WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
    return row["cnt"] if row else 0


def pop_oldest_messages(user_db_id: int, n: int) -> list[dict[str, Any]]:
    """
    Delete the oldest N messages and return them (for summarisation).
    Returns list of {role, content} dicts.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content
            FROM context_messages
            WHERE user_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (user_db_id, n),
        ).fetchall()
        if rows:
            ids = [r["id"] for r in rows]
            placeholders = ",".join("?" * len(ids))
            conn.execute(
                f"DELETE FROM context_messages WHERE id IN ({placeholders})",
                ids,
            )
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def get_last_activity(user_db_id: int) -> str | None:
    """Return the created_at timestamp of the most recent message, or None."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT created_at
            FROM context_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_db_id,),
        ).fetchone()
    return row["created_at"] if row else None


# ── Summary ───────────────────────────────────────────────────────────────────

def get_summary(user_db_id: int) -> str:
    """Return the stored summary text (empty string if none)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT summary FROM context_summary WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
    return row["summary"] if row else ""


def set_summary(user_db_id: int, summary: str) -> None:
    """Upsert summary for user."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO context_summary (user_id, summary, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE
                SET summary    = excluded.summary,
                    updated_at = excluded.updated_at
            """,
            (user_db_id, summary),
        )


def delete_summary(user_db_id: int) -> None:
    """Delete summary for user."""
    with get_connection() as conn:
        conn.execute("DELETE FROM context_summary WHERE user_id = ?", (user_db_id,))


# ── Context mode (stored on users table) ─────────────────────────────────────

def get_context_mode(telegram_id: int) -> str:
    """Return 'chat' or 'single' for a user (by telegram_id). Defaults to 'single'."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT context_mode FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
    return (row["context_mode"] or "single") if row else "single"


def set_context_mode(telegram_id: int, mode: str) -> None:
    """Update context_mode on users row (by telegram_id)."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET context_mode = ? WHERE telegram_id = ?",
            (mode, telegram_id),
        )
