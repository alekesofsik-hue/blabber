"""
Shared LanceDB helpers for vector-backed repositories.

Design:
- Resolve the data directory on each call so tests can override `LANCEDB_PATH`
- Keep the API low-level and domain-agnostic: open/create/add/search/delete/drop
- Let domain repositories decide whether LanceDB failures are fatal or soft-fail

Naming convention:
- The helper supports arbitrary table names.
- For new KB vector storage, prefer a shared domain table keyed by metadata
  columns such as `user_id`, `doc_id`, `chunk_uid`.
- Existing quotes tables keep their legacy per-user naming (`quotes_<user_db_id>`)
  to avoid changing behaviour during the migration.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pyarrow as pa

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    """Return the configured LanceDB data directory."""
    raw = os.environ.get("LANCEDB_PATH", str(_PROJECT_ROOT / "lancedb_data"))
    return Path(raw)


def _connect():
    """Create a LanceDB connection for the current configured data directory."""
    import lancedb

    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(data_dir))


def list_tables() -> list[str]:
    """Return all table names in the configured LanceDB database."""
    db = _connect()
    response = db.list_tables()
    return list(response.tables or [])


def table_exists(table_name: str) -> bool:
    """True if a table with the given name exists."""
    return table_name in list_tables()


def open_table(table_name: str, schema: pa.Schema):
    """Open an existing table or create it with the provided schema."""
    db = _connect()
    existing = db.list_tables().tables or []
    if table_name not in existing:
        db.create_table(table_name, schema=schema)
    return db.open_table(table_name)


def add_rows(table_name: str, schema: pa.Schema, rows: list[dict[str, Any]]) -> None:
    """Add rows to a table, creating it first if needed."""
    if not rows:
        return
    table = open_table(table_name, schema)
    table.add(rows)


def search_rows(
    table_name: str,
    schema: pa.Schema,
    query_vector: list[float],
    *,
    limit: int = 5,
    where: str | None = None,
) -> list[dict[str, Any]]:
    """Search a table by vector similarity and return LanceDB rows as dicts."""
    table = open_table(table_name, schema)
    query = table.search(query_vector)
    if where:
        query = query.where(where)
    return query.limit(limit).to_list()


def delete_rows(table_name: str, schema: pa.Schema, where: str) -> None:
    """Delete rows matching a predicate, creating the table first if needed."""
    table = open_table(table_name, schema)
    table.delete(where)


def drop_table(table_name: str) -> bool:
    """Drop a table if it exists. Returns True if dropped, False if absent."""
    db = _connect()
    existing = db.list_tables().tables or []
    if table_name not in existing:
        return False
    db.drop_table(table_name)
    return True
