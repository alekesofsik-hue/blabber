from __future__ import annotations

import pyarrow as pa

from repositories import lancedb_store


def _schema(dim: int = 3) -> pa.Schema:
    return pa.schema([
        pa.field("id", pa.string()),
        pa.field("text", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), dim)),
    ])


def test_open_add_search_delete_drop(tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))

    table_name = "test_vectors"
    schema = _schema()

    assert not lancedb_store.table_exists(table_name)

    table = lancedb_store.open_table(table_name, schema)
    assert table is not None
    assert lancedb_store.table_exists(table_name)
    assert table_name in lancedb_store.list_tables()

    lancedb_store.add_rows(
        table_name,
        schema,
        [
            {"id": "a", "text": "alpha", "vector": [1.0, 0.0, 0.0]},
            {"id": "b", "text": "beta", "vector": [0.0, 1.0, 0.0]},
        ],
    )

    results = lancedb_store.search_rows(
        table_name,
        schema,
        [1.0, 0.0, 0.0],
        limit=2,
    )
    assert len(results) == 2
    assert results[0]["id"] == "a"

    lancedb_store.delete_rows(table_name, schema, "id = 'a'")
    after_delete = lancedb_store.search_rows(
        table_name,
        schema,
        [1.0, 0.0, 0.0],
        limit=5,
    )
    assert [row["id"] for row in after_delete] == ["b"]

    assert lancedb_store.drop_table(table_name) is True
    assert not lancedb_store.table_exists(table_name)
    assert lancedb_store.drop_table(table_name) is False
