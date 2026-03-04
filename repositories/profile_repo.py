"""
Profile repository — CRUD for the user_profiles table (long-term memory D).
"""

from __future__ import annotations

from database import get_connection


def get_facts(user_db_id: int) -> list[str]:
    """Return all facts for user, ordered oldest-first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT fact FROM user_profiles WHERE user_id = ? ORDER BY id ASC",
            (user_db_id,),
        ).fetchall()
    return [r["fact"] for r in rows]


def get_facts_with_ids(user_db_id: int) -> list[dict]:
    """Return all facts with their DB ids (for delete-by-id)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, fact FROM user_profiles WHERE user_id = ? ORDER BY id ASC",
            (user_db_id,),
        ).fetchall()
    return [{"id": r["id"], "fact": r["fact"]} for r in rows]


def add_fact(user_db_id: int, fact: str) -> bool:
    """Insert fact. Returns True if inserted, False if duplicate."""
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM user_profiles WHERE user_id = ? AND fact = ?",
            (user_db_id, fact),
        ).fetchone()
        if exists:
            return False
        conn.execute(
            "INSERT INTO user_profiles (user_id, fact) VALUES (?, ?)",
            (user_db_id, fact),
        )
    return True


def delete_fact_by_id(profile_id: int, user_db_id: int) -> bool:
    """Delete a fact by its id (safety-checked against user_db_id)."""
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM user_profiles WHERE id = ? AND user_id = ?",
            (profile_id, user_db_id),
        )
    return cur.rowcount > 0


def delete_all_facts(user_db_id: int) -> None:
    """Delete all facts for user."""
    with get_connection() as conn:
        conn.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_db_id,))


def count_facts(user_db_id: int) -> int:
    """Count stored facts for user."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM user_profiles WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
    return row["cnt"] if row else 0
