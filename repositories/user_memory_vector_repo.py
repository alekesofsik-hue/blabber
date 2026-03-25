"""
User memory vector repository — shared LanceDB table for semantic user memory.

This repository is intentionally storage-focused:
- it knows how semantic user memory rows are stored in LanceDB
- it does not decide insert/update/skip policy
- it isolates data by internal `user_id`
- it supports both single-row upsert and bulk reindex operations
"""

from __future__ import annotations

from typing import Any

import pyarrow as pa

from repositories import lancedb_store

TABLE_NAME = "user_memory_vectors"
EMBEDDING_DIM = 1536  # text-embedding-3-small

USER_MEMORY_VECTOR_SCHEMA = pa.schema([
    pa.field("id", pa.string()),
    pa.field("user_id", pa.int64()),
    pa.field("profile_id", pa.int64()),
    pa.field("kind", pa.string()),
    pa.field("text", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
])


def _normalize_row(*, user_db_id: int, item: dict[str, Any]) -> dict[str, Any]:
    """Convert a service item into a LanceDB row."""
    profile_id = int(item["profile_id"])
    return {
        "id": str(profile_id),
        "user_id": int(user_db_id),
        "profile_id": profile_id,
        "kind": str(item["kind"]),
        "text": str(item["text"]),
        "vector": item["vector"],
    }


def upsert_item(
    *,
    user_db_id: int,
    profile_id: int,
    kind: str,
    text: str,
    vector: list[float],
) -> bool:
    """
    Upsert one semantic memory row into the shared LanceDB table.

    Returns True when the row was written.
    """
    written = upsert_items(
        user_db_id=user_db_id,
        items=[{
            "profile_id": profile_id,
            "kind": kind,
            "text": text,
            "vector": vector,
        }],
    )
    return written == 1


def upsert_items(*, user_db_id: int, items: list[dict[str, Any]]) -> int:
    """
    Bulk upsert semantic memory rows for a single user.

    Expected item shape:
      {
        "profile_id": int,
        "kind": str,
        "text": str,
        "vector": list[float],
      }
    """
    if not items:
        return 0

    profile_ids = [int(item["profile_id"]) for item in items]
    quoted = ",".join(str(pid) for pid in profile_ids)
    lancedb_store.delete_rows(
        TABLE_NAME,
        USER_MEMORY_VECTOR_SCHEMA,
        f"user_id = {int(user_db_id)} AND profile_id IN ({quoted})",
    )

    rows = [_normalize_row(user_db_id=user_db_id, item=item) for item in items]
    lancedb_store.add_rows(TABLE_NAME, USER_MEMORY_VECTOR_SCHEMA, rows)
    return len(rows)


def replace_all_for_user(*, user_db_id: int, items: list[dict[str, Any]]) -> int:
    """
    Replace the full semantic memory index for one user.

    This is the safest low-level primitive for reindex operations because it can
    remove stale LanceDB rows that no longer exist in SQLite.
    """
    delete_all_for_user(user_db_id=user_db_id)
    if not items:
        return 0
    rows = [_normalize_row(user_db_id=user_db_id, item=item) for item in items]
    lancedb_store.add_rows(TABLE_NAME, USER_MEMORY_VECTOR_SCHEMA, rows)
    return len(rows)


def search_by_vector(
    *,
    user_db_id: int,
    query_vector: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Search semantic user memory rows for one user.

    Returns LanceDB rows enriched with distance for service-layer ranking.
    """
    results = lancedb_store.search_rows(
        TABLE_NAME,
        USER_MEMORY_VECTOR_SCHEMA,
        query_vector,
        limit=top_k,
        where=f"user_id = {int(user_db_id)}",
    )
    return [
        {
            "profile_id": row["profile_id"],
            "kind": row["kind"],
            "text": row["text"],
            "vector": row.get("vector"),
            "distance": row.get("_distance", 0.0),
        }
        for row in results
    ]


def delete_by_profile_id(*, user_db_id: int, profile_id: int) -> None:
    """Delete one semantic memory row for a user by linked profile id."""
    lancedb_store.delete_rows(
        TABLE_NAME,
        USER_MEMORY_VECTOR_SCHEMA,
        f"user_id = {int(user_db_id)} AND profile_id = {int(profile_id)}",
    )


def delete_all_for_user(*, user_db_id: int) -> None:
    """Delete all semantic memory rows for a single user."""
    lancedb_store.delete_rows(
        TABLE_NAME,
        USER_MEMORY_VECTOR_SCHEMA,
        f"user_id = {int(user_db_id)}",
    )

