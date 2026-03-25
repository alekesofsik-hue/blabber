"""
Profile repository — CRUD for the user_profiles table (long-term memory D).
"""

from __future__ import annotations

from database import get_connection


def get_facts(user_db_id: int) -> list[str]:
    """Return all facts for user, ordered oldest-first (backward-compatible)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT fact FROM user_profiles WHERE user_id = ? ORDER BY id ASC",
            (user_db_id,),
        ).fetchall()
    return [r["fact"] for r in rows]


def get_facts_with_ids(user_db_id: int) -> list[dict]:
    """Return all facts with their DB ids (for delete-by-id). Backward-compatible."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, fact FROM user_profiles WHERE user_id = ? ORDER BY id ASC",
            (user_db_id,),
        ).fetchall()
    return [{"id": r["id"], "fact": r["fact"]} for r in rows]


def get_items_with_ids(user_db_id: int) -> list[dict]:
    """Return all profile items with their DB ids (includes kind)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, kind, fact FROM user_profiles WHERE user_id = ? ORDER BY id ASC",
            (user_db_id,),
        ).fetchall()
    return [{"id": r["id"], "kind": r["kind"], "fact": r["fact"]} for r in rows]


def get_item_by_id(profile_id: int, user_db_id: int) -> dict | None:
    """Return one profile item by id if it belongs to the user."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, kind, fact
            FROM user_profiles
            WHERE id = ? AND user_id = ?
            """,
            (profile_id, user_db_id),
        ).fetchone()
    if not row:
        return None
    return {"id": row["id"], "kind": row["kind"], "fact": row["fact"]}


def add_fact(user_db_id: int, fact: str) -> bool:
    """Insert fact. Returns True if inserted, False if duplicate. Backward-compatible."""
    return add_item(user_db_id, fact=fact, kind="fact")


def add_item_returning_id(user_db_id: int, *, fact: str, kind: str = "fact") -> int | None:
    """
    Insert profile item with kind and return its id.

    Returns None if an exact duplicate already exists.
    """
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT id FROM user_profiles WHERE user_id = ? AND fact = ?",
            (user_db_id, fact),
        ).fetchone()
        if exists:
            return None
        conn.execute(
            "INSERT INTO user_profiles (user_id, kind, fact) VALUES (?, ?, ?)",
            (user_db_id, kind, fact),
        )
        row = conn.execute("SELECT last_insert_rowid() AS id").fetchone()
    return row["id"] if row else None


def add_item(user_db_id: int, *, fact: str, kind: str = "fact") -> bool:
    """Insert profile item with kind. Returns True if inserted, False if duplicate."""
    return add_item_returning_id(user_db_id, fact=fact, kind=kind) is not None


def update_item_text(profile_id: int, user_db_id: int, *, fact: str) -> bool:
    """Update the text of one existing profile item owned by the user."""
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE user_profiles
            SET fact = ?
            WHERE id = ? AND user_id = ?
            """,
            (fact, profile_id, user_db_id),
        )
    return cur.rowcount > 0


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
