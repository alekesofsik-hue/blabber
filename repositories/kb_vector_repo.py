"""
KB vector repository — shared LanceDB table for semantic KB storage.

This repository is intentionally storage-focused:
- it knows how KB vectors are stored in LanceDB
- it does not know about retrieval ranking policy
- it returns chunk_uids so the service layer can enrich results from SQLite
"""

from __future__ import annotations

from typing import Any

import pyarrow as pa

from repositories import lancedb_store

TABLE_NAME = "kb_vectors"
EMBEDDING_DIM = 1536  # text-embedding-3-small

KB_VECTOR_SCHEMA = pa.schema([
    pa.field("id", pa.string()),
    pa.field("user_id", pa.int64()),
    pa.field("doc_id", pa.int64()),
    pa.field("chunk_uid", pa.string()),
    pa.field("chunk_idx", pa.int32()),
    pa.field("text", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
])


def upsert_chunks(
    *,
    user_db_id: int,
    doc_id: int,
    chunks: list[dict[str, Any]],
) -> int:
    """
    Upsert KB chunk vectors into the shared LanceDB table.

    Expected chunk shape:
      {
        "chunk_uid": str,
        "chunk_idx": int,
        "content": str,
        "vector": list[float],
      }
    """
    if not chunks:
        return 0

    chunk_uids = [str(chunk["chunk_uid"]) for chunk in chunks]
    quoted = ",".join(f"'{uid}'" for uid in chunk_uids)
    lancedb_store.delete_rows(TABLE_NAME, KB_VECTOR_SCHEMA, f"chunk_uid IN ({quoted})")

    rows = [
        {
            "id": str(chunk["chunk_uid"]),
            "user_id": int(user_db_id),
            "doc_id": int(doc_id),
            "chunk_uid": str(chunk["chunk_uid"]),
            "chunk_idx": int(chunk["chunk_idx"]),
            "text": str(chunk["content"]),
            "vector": chunk["vector"],
        }
        for chunk in chunks
    ]
    lancedb_store.add_rows(TABLE_NAME, KB_VECTOR_SCHEMA, rows)
    return len(rows)


def search_by_vector(
    *,
    user_db_id: int,
    query_vector: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Search KB vectors for a user and return chunk_uids with distances.
    """
    results = lancedb_store.search_rows(
        TABLE_NAME,
        KB_VECTOR_SCHEMA,
        query_vector,
        limit=top_k,
        where=f"user_id = {int(user_db_id)}",
    )
    return [
        {
            "chunk_uid": row["chunk_uid"],
            "distance": row.get("_distance", 0.0),
            "doc_id": row["doc_id"],
            "chunk_idx": row["chunk_idx"],
            "text": row["text"],
        }
        for row in results
    ]


def delete_by_doc(*, user_db_id: int, doc_id: int) -> None:
    """Delete all vectors for a single KB document."""
    lancedb_store.delete_rows(
        TABLE_NAME,
        KB_VECTOR_SCHEMA,
        f"user_id = {int(user_db_id)} AND doc_id = {int(doc_id)}",
    )


def delete_all_for_user(*, user_db_id: int) -> None:
    """Delete all KB vectors for a user."""
    lancedb_store.delete_rows(
        TABLE_NAME,
        KB_VECTOR_SCHEMA,
        f"user_id = {int(user_db_id)}",
    )
