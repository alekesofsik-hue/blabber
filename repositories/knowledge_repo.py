"""
Knowledge base repository — CRUD for kb_documents and kb_chunks tables.
"""

from __future__ import annotations

from typing import Any

from database import get_connection


# ── Documents ─────────────────────────────────────────────────────────────────

def add_document(user_db_id: int, name: str, size_bytes: int, chunk_count: int) -> int:
    """Insert a document record and return its new id."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO kb_documents (user_id, name, size_bytes, chunk_count) VALUES (?, ?, ?, ?)",
            (user_db_id, name, size_bytes, chunk_count),
        )
    return cur.lastrowid


def get_documents(user_db_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, size_bytes, chunk_count, created_at
            FROM kb_documents
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_db_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_document(doc_id: int, user_db_id: int) -> bool:
    """Delete a document (and its chunks via CASCADE). Returns True if found."""
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM kb_documents WHERE id = ? AND user_id = ?",
            (doc_id, user_db_id),
        )
    return cur.rowcount > 0


def delete_all_documents(user_db_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM kb_documents WHERE user_id = ?", (user_db_id,))


def count_documents(user_db_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM kb_documents WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
    return row["cnt"] if row else 0


# ── Chunks ────────────────────────────────────────────────────────────────────

def add_chunks(
    doc_id: int,
    user_db_id: int,
    chunks: list[str],
    embeddings: list[bytes | None] | None = None,
) -> None:
    if embeddings is None:
        embeddings = [None] * len(chunks)
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO kb_chunks (doc_id, user_id, content, chunk_idx, embedding) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (doc_id, user_db_id, text, idx, emb)
                for idx, (text, emb) in enumerate(zip(chunks, embeddings))
            ],
        )


def get_all_chunks(user_db_id: int) -> list[dict[str, Any]]:
    """Return all chunks for user, joined with their document name."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.content, c.chunk_idx, c.embedding, d.name AS doc_name
            FROM   kb_chunks c
            JOIN   kb_documents d ON d.id = c.doc_id
            WHERE  c.user_id = ?
            ORDER  BY c.doc_id ASC, c.chunk_idx ASC
            """,
            (user_db_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def count_chunks(user_db_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM kb_chunks WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
    return row["cnt"] if row else 0
