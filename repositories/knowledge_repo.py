"""
Knowledge base repository — CRUD for kb_documents and kb_chunks tables.
"""

from __future__ import annotations

import uuid
from typing import Any

from database import get_connection


# ── Documents ─────────────────────────────────────────────────────────────────

def add_document(
    user_db_id: int,
    name: str,
    size_bytes: int,
    chunk_count: int,
    *,
    source_type: str = "file",
    source_url: str | None = None,
) -> int:
    """Insert a document record and return its new id."""
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO kb_documents (user_id, name, size_bytes, chunk_count, source_type, source_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_db_id, name, size_bytes, chunk_count, source_type, source_url),
        )
    return cur.lastrowid


def get_documents(user_db_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, size_bytes, chunk_count, source_type, source_url, created_at
            FROM kb_documents
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_db_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_document(doc_id: int, user_db_id: int) -> dict[str, Any] | None:
    """Return one KB document by id for the given user."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, size_bytes, chunk_count, source_type, source_url, created_at
            FROM kb_documents
            WHERE id = ? AND user_id = ?
            """,
            (doc_id, user_db_id),
        ).fetchone()
    return dict(row) if row else None


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
) -> list[str]:
    if embeddings is None:
        embeddings = [None] * len(chunks)
    if len(embeddings) != len(chunks):
        raise ValueError("Embeddings count must match chunks count")

    chunk_uids = [uuid.uuid4().hex for _ in chunks]
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO kb_chunks (doc_id, user_id, content, chunk_idx, embedding, chunk_uid) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (doc_id, user_db_id, text, idx, emb, chunk_uid)
                for idx, ((text, emb), chunk_uid) in enumerate(zip(zip(chunks, embeddings), chunk_uids))
            ],
        )
    return chunk_uids


def get_all_chunks(user_db_id: int) -> list[dict[str, Any]]:
    """Return all chunks for user, joined with their document name."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.doc_id, c.chunk_uid, c.content, c.chunk_idx, c.embedding, d.name AS doc_name
            FROM   kb_chunks c
            JOIN   kb_documents d ON d.id = c.doc_id
            WHERE  c.user_id = ?
            ORDER  BY c.doc_id ASC, c.chunk_idx ASC
            """,
            (user_db_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_chunks_by_doc(doc_id: int, user_db_id: int) -> list[dict[str, Any]]:
    """Return all chunks for a document, including stable chunk_uid."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.doc_id, c.chunk_uid, c.content, c.chunk_idx, c.embedding, d.name AS doc_name
            FROM   kb_chunks c
            JOIN   kb_documents d ON d.id = c.doc_id
            WHERE  c.user_id = ? AND c.doc_id = ?
            ORDER  BY c.chunk_idx ASC
            """,
            (user_db_id, doc_id),
        ).fetchall()
    return [dict(r) for r in rows]


def get_chunks_by_uids(user_db_id: int, chunk_uids: list[str]) -> list[dict[str, Any]]:
    """Return chunks matching the provided stable chunk_uids."""
    if not chunk_uids:
        return []
    placeholders = ",".join("?" * len(chunk_uids))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT c.id, c.doc_id, c.chunk_uid, c.content, c.chunk_idx, c.embedding, d.name AS doc_name
            FROM   kb_chunks c
            JOIN   kb_documents d ON d.id = c.doc_id
            WHERE  c.user_id = ? AND c.chunk_uid IN ({placeholders})
            ORDER  BY c.doc_id ASC, c.chunk_idx ASC
            """,
            (user_db_id, *chunk_uids),
        ).fetchall()
    return [dict(r) for r in rows]


def count_chunks(user_db_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM kb_chunks WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
    return row["cnt"] if row else 0


def update_chunk_embeddings(
    user_db_id: int,
    items: list[tuple[str, bytes | None]],
) -> int:
    """
    Update legacy embedding BLOBs for existing chunks by stable chunk_uid.

    Returns the number of requested updates; callers rely on stable chunk_uids
    and do not need per-row rowcount semantics from sqlite executemany.
    """
    if not items:
        return 0
    with get_connection() as conn:
        conn.executemany(
            """
            UPDATE kb_chunks
            SET embedding = ?
            WHERE user_id = ? AND chunk_uid = ?
            """,
            [(embedding, user_db_id, chunk_uid) for chunk_uid, embedding in items],
        )
    return len(items)
