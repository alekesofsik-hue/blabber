"""
Quotes repository — dual-storage: SQLite (metadata) + LanceDB (vectors).

SQLite keeps lightweight metadata (id, text, timestamp) for listing and
random picks without loading vectors. LanceDB stores the embedding vectors
for semantic similarity search.

LanceDB tables are stored per-user in a shared directory so each user's
collection is isolated and can be opened/closed cheaply.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import pyarrow as pa

from database import get_connection
from repositories import lancedb_store

logger = logging.getLogger("blabber")

EMBEDDING_DIM = 1536  # text-embedding-3-small
_QUOTES_SCHEMA = pa.schema([
    pa.field("id", pa.string()),
    pa.field("text", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
])


# ── LanceDB helpers ───────────────────────────────────────────────────────────

def _get_lance_table(user_db_id: int):
    """
    Open (or create) the LanceDB table for a user's quotes collection.

    Table name: quotes_{user_db_id}
    Schema: id (str), text (str), vector (fixed-size list of float32)
    """
    table_name = f"quotes_{user_db_id}"
    return lancedb_store.open_table(table_name, _QUOTES_SCHEMA)


# ── SQLite helpers ────────────────────────────────────────────────────────────

def _get_user_db_id(telegram_id: int) -> int | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return row["id"] if row else None


# ── Write operations ──────────────────────────────────────────────────────────

def add_quote(
    telegram_id: int,
    text: str,
    vector: list[float] | None,
) -> str:
    """
    Persist a quote in SQLite + LanceDB.

    Returns the lance_id (UUID string) that links both records.
    Raises ValueError if user not found.
    """
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        raise ValueError(f"User not found: telegram_id={telegram_id}")

    lance_id = uuid.uuid4().hex

    # SQLite: lightweight metadata
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quotes (user_id, lance_id, text) VALUES (?, ?, ?)",
            (user_db_id, lance_id, text),
        )

    # LanceDB: vector index
    if vector is not None:
        try:
            lancedb_store.add_rows(
                f"quotes_{user_db_id}",
                _QUOTES_SCHEMA,
                [{"id": lance_id, "text": text, "vector": vector}],
            )
        except Exception as exc:
            logger.warning(
                "quotes_lance_add_failed",
                extra={"error": str(exc)[:200], "lance_id": lance_id},
            )

    return lance_id


def delete_quote(telegram_id: int, quote_id: int) -> bool:
    """Delete quote by SQLite id. Returns True if found and deleted."""
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return False

    with get_connection() as conn:
        row = conn.execute(
            "SELECT lance_id FROM quotes WHERE id = ? AND user_id = ?",
            (quote_id, user_db_id),
        ).fetchone()
        if not row:
            return False
        lance_id = row["lance_id"]
        conn.execute(
            "DELETE FROM quotes WHERE id = ? AND user_id = ?",
            (quote_id, user_db_id),
        )

    # Remove from LanceDB
    try:
        lancedb_store.delete_rows(
            f"quotes_{user_db_id}",
            _QUOTES_SCHEMA,
            f"id = '{lance_id}'",
        )
    except Exception as exc:
        logger.warning(
            "quotes_lance_delete_failed",
            extra={"error": str(exc)[:200], "lance_id": lance_id},
        )

    return True


def delete_all_quotes(telegram_id: int) -> int:
    """Delete all quotes for user. Returns count deleted."""
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return 0

    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM quotes WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
        count = row["cnt"] if row else 0
        conn.execute("DELETE FROM quotes WHERE user_id = ?", (user_db_id,))

    # Drop LanceDB table entirely (faster than per-row delete)
    try:
        lancedb_store.drop_table(f"quotes_{user_db_id}")
    except Exception as exc:
        logger.warning(
            "quotes_lance_drop_failed",
            extra={"error": str(exc)[:200]},
        )

    return count


# ── Read operations ───────────────────────────────────────────────────────────

def get_quote_count(telegram_id: int) -> int:
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return 0
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM quotes WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
        return row["cnt"] if row else 0


def get_recent_quotes(telegram_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """Return last N quotes (newest first)."""
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, lance_id, text, added_at
            FROM quotes
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_db_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_quotes_page(telegram_id: int, offset: int, limit: int) -> list[dict[str, Any]]:
    """Return a page of quotes (newest first), same order as get_recent_quotes."""
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, lance_id, text, added_at
            FROM quotes
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (user_db_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def get_random_quote(telegram_id: int) -> dict[str, Any] | None:
    """Return a single random quote."""
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, lance_id, text, added_at
            FROM quotes
            WHERE user_id = ?
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (user_db_id,),
        ).fetchone()
        return dict(row) if row else None


def semantic_search(
    telegram_id: int,
    query_vector: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Semantic similarity search over user's quotes via LanceDB.

    Returns list of dicts with keys: id (lance_id), text, _distance.
    """
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return []

    try:
        results = lancedb_store.search_rows(
            f"quotes_{user_db_id}",
            _QUOTES_SCHEMA,
            query_vector,
            limit=top_k,
        )
        return [
            {"lance_id": r["id"], "text": r["text"], "distance": r.get("_distance", 0.0)}
            for r in results
        ]
    except Exception as exc:
        logger.warning(
            "quotes_semantic_search_failed",
            extra={"error": str(exc)[:200]},
        )
        return []


def get_quote_by_lance_id(telegram_id: int, lance_id: str) -> dict[str, Any] | None:
    """SQLite-метаданные строки по lance_id (для обогащения семантического поиска)."""
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, lance_id, text, added_at
            FROM quotes
            WHERE user_id = ? AND lance_id = ?
            """,
            (user_db_id, lance_id),
        ).fetchone()
        return dict(row) if row else None


def text_search(telegram_id: int, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Simple keyword search in SQLite (fallback when embeddings unavailable)."""
    user_db_id = _get_user_db_id(telegram_id)
    if user_db_id is None:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, lance_id, text, added_at
            FROM quotes
            WHERE user_id = ? AND text LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_db_id, f"%{query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]
