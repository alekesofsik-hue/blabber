"""
History-day memory repository — shared LanceDB table for scenario user messages.

This repository is intentionally storage-focused:
- it stores only user-authored text messages for the feature scenario
- it isolates rows by internal `user_id`
- it supports semantic search with optional scenario filtering
- it keeps the API low-level so service layer can decide skip/fallback policy
"""

from __future__ import annotations

from typing import Any

import pyarrow as pa

from repositories import lancedb_store

TABLE_NAME = "history_day_message_memory"
EMBEDDING_DIM = 1536  # text-embedding-3-small
DEFAULT_TOP_K = 5
MAX_TOP_K = 20

HISTORY_DAY_MEMORY_SCHEMA = pa.schema([
    pa.field("id", pa.string()),
    pa.field("user_id", pa.int64()),
    pa.field("source_id", pa.string()),
    pa.field("text", pa.string()),
    pa.field("scenario_tag", pa.string()),
    pa.field("command_name", pa.string()),
    pa.field("source_kind", pa.string()),
    pa.field("event_date", pa.string()),
    pa.field("created_at", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
])


def _quote(value: str) -> str:
    """Quote a string literal for LanceDB SQL-like where clauses."""
    return "'" + str(value).replace("'", "''") + "'"


def _normalize_row(*, user_db_id: int, item: dict[str, Any]) -> dict[str, Any]:
    source_id = str(item["source_id"])
    return {
        "id": source_id,
        "user_id": int(user_db_id),
        "source_id": source_id,
        "text": str(item["text"]),
        "scenario_tag": str(item.get("scenario_tag") or ""),
        "command_name": str(item.get("command_name") or ""),
        "source_kind": str(item.get("source_kind") or "user_message"),
        "event_date": str(item.get("event_date") or ""),
        "created_at": str(item["created_at"]),
        "vector": item["vector"],
    }


def upsert_message(
    *,
    user_db_id: int,
    source_id: str,
    text: str,
    vector: list[float],
    scenario_tag: str,
    created_at: str,
    command_name: str = "",
    source_kind: str = "user_message",
    event_date: str = "",
) -> bool:
    """Upsert one scenario user message into the shared LanceDB table."""
    written = upsert_messages(
        user_db_id=user_db_id,
        items=[{
            "source_id": source_id,
            "text": text,
            "vector": vector,
            "scenario_tag": scenario_tag,
            "created_at": created_at,
            "command_name": command_name,
            "source_kind": source_kind,
            "event_date": event_date,
        }],
    )
    return written == 1


def upsert_messages(*, user_db_id: int, items: list[dict[str, Any]]) -> int:
    """Bulk upsert scenario user messages for one user."""
    if not items:
        return 0

    source_ids = [str(item["source_id"]) for item in items]
    quoted = ",".join(_quote(source_id) for source_id in source_ids)
    lancedb_store.delete_rows(
        TABLE_NAME,
        HISTORY_DAY_MEMORY_SCHEMA,
        f"user_id = {int(user_db_id)} AND source_id IN ({quoted})",
    )

    rows = [_normalize_row(user_db_id=user_db_id, item=item) for item in items]
    lancedb_store.add_rows(TABLE_NAME, HISTORY_DAY_MEMORY_SCHEMA, rows)
    return len(rows)


def search_by_vector(
    *,
    user_db_id: int,
    query_vector: list[float],
    top_k: int = DEFAULT_TOP_K,
    scenario_tag: str | None = None,
) -> list[dict[str, Any]]:
    """Search scenario memory rows for one user."""
    top_k = max(1, min(int(top_k), MAX_TOP_K))
    where = f"user_id = {int(user_db_id)}"
    if scenario_tag:
        where += f" AND scenario_tag = {_quote(scenario_tag)}"

    results = lancedb_store.search_rows(
        TABLE_NAME,
        HISTORY_DAY_MEMORY_SCHEMA,
        query_vector,
        limit=top_k,
        where=where,
    )
    return [
        {
            "source_id": row["source_id"],
            "text": row["text"],
            "scenario_tag": row["scenario_tag"],
            "command_name": row.get("command_name", ""),
            "source_kind": row.get("source_kind", ""),
            "event_date": row.get("event_date", ""),
            "created_at": row["created_at"],
            "vector": row.get("vector"),
            "distance": row.get("_distance", 0.0),
        }
        for row in results
    ]


def list_for_user(*, user_db_id: int, scenario_tag: str | None = None) -> list[dict[str, Any]]:
    """
    Return all stored scenario memory rows for one user.

    Used for lightweight pruning and diagnostics in the service layer.
    """
    table = lancedb_store.open_table(TABLE_NAME, HISTORY_DAY_MEMORY_SCHEMA)
    rows = table.to_arrow().to_pylist()
    filtered = [row for row in rows if int(row.get("user_id", -1)) == int(user_db_id)]
    if scenario_tag:
        filtered = [row for row in filtered if (row.get("scenario_tag") or "") == scenario_tag]
    filtered.sort(key=lambda row: str(row.get("created_at") or ""))
    return filtered


def delete_by_source_ids(*, user_db_id: int, source_ids: list[str]) -> None:
    """Delete one or more stored messages for a user by source ids."""
    if not source_ids:
        return
    quoted = ",".join(_quote(source_id) for source_id in source_ids)
    lancedb_store.delete_rows(
        TABLE_NAME,
        HISTORY_DAY_MEMORY_SCHEMA,
        f"user_id = {int(user_db_id)} AND source_id IN ({quoted})",
    )


def delete_all_for_user(*, user_db_id: int, scenario_tag: str | None = None) -> None:
    """Delete all scenario memory rows for a user, optionally scoped by tag."""
    where = f"user_id = {int(user_db_id)}"
    if scenario_tag:
        where += f" AND scenario_tag = {_quote(scenario_tag)}"
    lancedb_store.delete_rows(TABLE_NAME, HISTORY_DAY_MEMORY_SCHEMA, where)
