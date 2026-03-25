from __future__ import annotations

from repositories import kb_vector_repo


def _vector(axis: int = 0, dim: int = kb_vector_repo.EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_upsert_search_and_delete_by_doc(tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))

    inserted = kb_vector_repo.upsert_chunks(
        user_db_id=1,
        doc_id=10,
        chunks=[
            {
                "chunk_uid": "c1",
                "chunk_idx": 0,
                "content": "alpha chunk",
                "vector": _vector(0),
            },
            {
                "chunk_uid": "c2",
                "chunk_idx": 1,
                "content": "beta chunk",
                "vector": _vector(1),
            },
        ],
    )
    assert inserted == 2

    results = kb_vector_repo.search_by_vector(user_db_id=1, query_vector=_vector(0), top_k=5)
    assert len(results) == 2
    assert results[0]["chunk_uid"] == "c1"

    kb_vector_repo.delete_by_doc(user_db_id=1, doc_id=10)
    assert kb_vector_repo.search_by_vector(user_db_id=1, query_vector=_vector(0), top_k=5) == []


def test_search_is_scoped_to_user(tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))

    kb_vector_repo.upsert_chunks(
        user_db_id=1,
        doc_id=10,
        chunks=[
            {
                "chunk_uid": "u1_chunk",
                "chunk_idx": 0,
                "content": "first user chunk",
                "vector": _vector(0),
            }
        ],
    )
    kb_vector_repo.upsert_chunks(
        user_db_id=2,
        doc_id=20,
        chunks=[
            {
                "chunk_uid": "u2_chunk",
                "chunk_idx": 0,
                "content": "second user chunk",
                "vector": _vector(0),
            }
        ],
    )

    results = kb_vector_repo.search_by_vector(user_db_id=1, query_vector=_vector(0), top_k=10)
    assert [row["chunk_uid"] for row in results] == ["u1_chunk"]

    kb_vector_repo.delete_all_for_user(user_db_id=1)
    assert kb_vector_repo.search_by_vector(user_db_id=1, query_vector=_vector(0), top_k=10) == []
    assert [row["chunk_uid"] for row in kb_vector_repo.search_by_vector(user_db_id=2, query_vector=_vector(0), top_k=10)] == ["u2_chunk"]
