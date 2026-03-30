"""
Knowledge base repository — CRUD for kb_documents and kb_chunks tables.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from database import get_connection


def _json_loads_or_none(value: str | None) -> Any:
    if value in (None, ""):
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


def _decode_document_row(row: dict[str, Any]) -> dict[str, Any]:
    row["doc_has_tables"] = bool(row.get("doc_has_tables"))
    row["doc_has_headings"] = bool(row.get("doc_has_headings"))
    row["doc_structure_json"] = _json_loads_or_none(row.get("doc_structure_json"))
    row["doc_metadata_json"] = _json_loads_or_none(row.get("doc_metadata_json"))
    row["summary_topics_json"] = _json_loads_or_none(row.get("summary_topics_json"))
    row["summary_questions_json"] = _json_loads_or_none(row.get("summary_questions_json"))
    return row


def _decode_chunk_row(row: dict[str, Any]) -> dict[str, Any]:
    row["is_table"] = bool(row.get("is_table"))
    row["heading_path_json"] = _json_loads_or_none(row.get("heading_path_json"))
    row["meta_json"] = _json_loads_or_none(row.get("meta_json"))
    return row


# ── Documents ─────────────────────────────────────────────────────────────────

def add_document(
    user_db_id: int,
    name: str,
    size_bytes: int,
    chunk_count: int,
    *,
    source_type: str = "file",
    source_url: str | None = None,
    parser_backend: str | None = None,
    parser_mode: str | None = None,
    parser_version: str | None = None,
    source_format: str | None = None,
    doc_structure: dict[str, Any] | None = None,
    doc_metadata: dict[str, Any] | None = None,
    doc_has_tables: bool = False,
    doc_has_headings: bool = False,
    doc_page_count: int | None = None,
    summary_status: str = "pending",
) -> int:
    """Insert a document record and return its new id."""
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO kb_documents (
                user_id, name, size_bytes, chunk_count, source_type, source_url,
                parser_backend, parser_mode, parser_version, source_format,
                doc_structure_json, doc_metadata_json, doc_has_tables,
                doc_has_headings, doc_page_count, summary_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_db_id,
                name,
                size_bytes,
                chunk_count,
                source_type,
                source_url,
                parser_backend,
                parser_mode,
                parser_version,
                source_format,
                json.dumps(doc_structure, ensure_ascii=True) if doc_structure is not None else None,
                json.dumps(doc_metadata, ensure_ascii=True) if doc_metadata is not None else None,
                1 if doc_has_tables else 0,
                1 if doc_has_headings else 0,
                doc_page_count,
                summary_status,
            ),
        )
    return cur.lastrowid


def get_documents(user_db_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id, name, size_bytes, chunk_count, source_type, source_url, created_at,
                parser_backend, parser_mode, parser_version, source_format,
                doc_structure_json, doc_metadata_json, doc_has_tables,
                doc_has_headings, doc_page_count, summary_text,
                summary_topics_json, summary_questions_json, summary_status,
                summary_generated_at, summary_error
            FROM kb_documents
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_db_id,),
        ).fetchall()
    return [_decode_document_row(dict(r)) for r in rows]


def get_document(doc_id: int, user_db_id: int) -> dict[str, Any] | None:
    """Return one KB document by id for the given user."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id, name, size_bytes, chunk_count, source_type, source_url, created_at,
                parser_backend, parser_mode, parser_version, source_format,
                doc_structure_json, doc_metadata_json, doc_has_tables,
                doc_has_headings, doc_page_count, summary_text,
                summary_topics_json, summary_questions_json, summary_status,
                summary_generated_at, summary_error
            FROM kb_documents
            WHERE id = ? AND user_id = ?
            """,
            (doc_id, user_db_id),
        ).fetchone()
    return _decode_document_row(dict(row)) if row else None


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
    chunk_metadata: list[dict[str, Any]] | None = None,
) -> list[str]:
    if embeddings is None:
        embeddings = [None] * len(chunks)
    if len(embeddings) != len(chunks):
        raise ValueError("Embeddings count must match chunks count")
    if chunk_metadata is None:
        chunk_metadata = [{} for _ in chunks]
    if len(chunk_metadata) != len(chunks):
        raise ValueError("Chunk metadata count must match chunks count")

    chunk_uids = [uuid.uuid4().hex for _ in chunks]
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO kb_chunks (
                doc_id, user_id, content, chunk_idx, embedding, chunk_uid,
                section_title, heading_path_json, page_from, page_to,
                block_type, is_table, table_id, meta_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    doc_id,
                    user_db_id,
                    text,
                    idx,
                    emb,
                    chunk_uid,
                    meta.get("section_title"),
                    json.dumps(meta.get("heading_path"), ensure_ascii=True)
                    if meta.get("heading_path") is not None else None,
                    meta.get("page_from"),
                    meta.get("page_to"),
                    meta.get("block_type"),
                    1 if meta.get("is_table") else 0,
                    meta.get("table_id"),
                    json.dumps(meta.get("meta"), ensure_ascii=True)
                    if meta.get("meta") is not None else None,
                )
                for idx, ((text, emb), chunk_uid, meta) in enumerate(
                    zip(zip(chunks, embeddings), chunk_uids, chunk_metadata)
                )
            ],
        )
    return chunk_uids


def get_all_chunks(user_db_id: int) -> list[dict[str, Any]]:
    """Return all chunks for user, joined with their document name."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id, c.doc_id, c.chunk_uid, c.content, c.chunk_idx, c.embedding,
                c.section_title, c.heading_path_json, c.page_from, c.page_to,
                c.block_type, c.is_table, c.table_id, c.meta_json,
                d.name AS doc_name
            FROM   kb_chunks c
            JOIN   kb_documents d ON d.id = c.doc_id
            WHERE  c.user_id = ?
            ORDER  BY c.doc_id ASC, c.chunk_idx ASC
            """,
            (user_db_id,),
        ).fetchall()
    return [_decode_chunk_row(dict(r)) for r in rows]


def get_chunks_by_doc(doc_id: int, user_db_id: int) -> list[dict[str, Any]]:
    """Return all chunks for a document, including stable chunk_uid."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id, c.doc_id, c.chunk_uid, c.content, c.chunk_idx, c.embedding,
                c.section_title, c.heading_path_json, c.page_from, c.page_to,
                c.block_type, c.is_table, c.table_id, c.meta_json,
                d.name AS doc_name
            FROM   kb_chunks c
            JOIN   kb_documents d ON d.id = c.doc_id
            WHERE  c.user_id = ? AND c.doc_id = ?
            ORDER  BY c.chunk_idx ASC
            """,
            (user_db_id, doc_id),
        ).fetchall()
    return [_decode_chunk_row(dict(r)) for r in rows]


def get_chunks_by_uids(user_db_id: int, chunk_uids: list[str]) -> list[dict[str, Any]]:
    """Return chunks matching the provided stable chunk_uids."""
    if not chunk_uids:
        return []
    placeholders = ",".join("?" * len(chunk_uids))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                c.id, c.doc_id, c.chunk_uid, c.content, c.chunk_idx, c.embedding,
                c.section_title, c.heading_path_json, c.page_from, c.page_to,
                c.block_type, c.is_table, c.table_id, c.meta_json,
                d.name AS doc_name
            FROM   kb_chunks c
            JOIN   kb_documents d ON d.id = c.doc_id
            WHERE  c.user_id = ? AND c.chunk_uid IN ({placeholders})
            ORDER  BY c.doc_id ASC, c.chunk_idx ASC
            """,
            (user_db_id, *chunk_uids),
        ).fetchall()
    return [_decode_chunk_row(dict(r)) for r in rows]


def count_chunks(user_db_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM kb_chunks WHERE user_id = ?",
            (user_db_id,),
        ).fetchone()
    return row["cnt"] if row else 0


def update_document_summary(
    doc_id: int,
    user_db_id: int,
    *,
    summary_text: str | None = None,
    summary_topics: list[str] | None = None,
    summary_questions: list[str] | None = None,
    summary_status: str,
    summary_generated_at: str | None = None,
    summary_error: str | None = None,
) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE kb_documents
            SET summary_text = ?,
                summary_topics_json = ?,
                summary_questions_json = ?,
                summary_status = ?,
                summary_generated_at = ?,
                summary_error = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                summary_text,
                json.dumps(summary_topics, ensure_ascii=True) if summary_topics is not None else None,
                json.dumps(summary_questions, ensure_ascii=True) if summary_questions is not None else None,
                summary_status,
                summary_generated_at,
                summary_error,
                doc_id,
                user_db_id,
            ),
        )
    return cur.rowcount > 0


def update_document_structured_fields(
    doc_id: int,
    user_db_id: int,
    *,
    parser_backend: str | None = None,
    parser_mode: str | None = None,
    parser_version: str | None = None,
    source_format: str | None = None,
    doc_structure: dict[str, Any] | None = None,
    doc_metadata: dict[str, Any] | None = None,
    doc_has_tables: bool | None = None,
    doc_has_headings: bool | None = None,
    doc_page_count: int | None = None,
) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE kb_documents
            SET parser_backend = COALESCE(?, parser_backend),
                parser_mode = COALESCE(?, parser_mode),
                parser_version = COALESCE(?, parser_version),
                source_format = COALESCE(?, source_format),
                doc_structure_json = COALESCE(?, doc_structure_json),
                doc_metadata_json = COALESCE(?, doc_metadata_json),
                doc_has_tables = COALESCE(?, doc_has_tables),
                doc_has_headings = COALESCE(?, doc_has_headings),
                doc_page_count = COALESCE(?, doc_page_count)
            WHERE id = ? AND user_id = ?
            """,
            (
                parser_backend,
                parser_mode,
                parser_version,
                source_format,
                json.dumps(doc_structure, ensure_ascii=True) if doc_structure is not None else None,
                json.dumps(doc_metadata, ensure_ascii=True) if doc_metadata is not None else None,
                (1 if doc_has_tables else 0) if doc_has_tables is not None else None,
                (1 if doc_has_headings else 0) if doc_has_headings is not None else None,
                doc_page_count,
                doc_id,
                user_db_id,
            ),
        )
    return cur.rowcount > 0


def update_chunk_structured_metadata(
    user_db_id: int,
    items: list[tuple[str, dict[str, Any]]],
) -> int:
    if not items:
        return 0
    with get_connection() as conn:
        conn.executemany(
            """
            UPDATE kb_chunks
            SET section_title = ?,
                heading_path_json = ?,
                page_from = ?,
                page_to = ?,
                block_type = ?,
                is_table = ?,
                table_id = ?,
                meta_json = ?
            WHERE user_id = ? AND chunk_uid = ?
            """,
            [
                (
                    meta.get("section_title"),
                    json.dumps(meta.get("heading_path"), ensure_ascii=True)
                    if meta.get("heading_path") is not None else None,
                    meta.get("page_from"),
                    meta.get("page_to"),
                    meta.get("block_type"),
                    1 if meta.get("is_table") else 0,
                    meta.get("table_id"),
                    json.dumps(meta.get("meta"), ensure_ascii=True)
                    if meta.get("meta") is not None else None,
                    user_db_id,
                    chunk_uid,
                )
                for chunk_uid, meta in items
            ],
        )
    return len(items)


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
