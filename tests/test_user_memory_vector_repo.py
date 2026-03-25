from __future__ import annotations

from database import get_connection
from repositories import user_memory_vector_repo, user_repo


def _create_user(db, telegram_id: int = 666001) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "memvec_tester", "MemVec", role_id)
    return telegram_id, user["id"]


def _vector(axis: int = 0, dim: int = user_memory_vector_repo.EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_upsert_and_search_user_memory_vectors(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    _telegram_id, user_db_id = _create_user(db)

    written = user_memory_vector_repo.upsert_item(
        user_db_id=user_db_id,
        profile_id=101,
        kind="fact",
        text="Меня зовут Алексей",
        vector=_vector(0),
    )

    assert written is True

    results = user_memory_vector_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(0),
        top_k=3,
    )
    assert len(results) == 1
    assert results[0]["profile_id"] == 101
    assert results[0]["kind"] == "fact"
    assert results[0]["text"] == "Меня зовут Алексей"


def test_delete_by_profile_id_removes_only_target(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    _telegram_id, user_db_id = _create_user(db, telegram_id=666002)

    user_memory_vector_repo.upsert_items(
        user_db_id=user_db_id,
        items=[
            {"profile_id": 201, "kind": "fact", "text": "Первый факт", "vector": _vector(0)},
            {"profile_id": 202, "kind": "fact", "text": "Второй факт", "vector": _vector(1)},
        ],
    )

    user_memory_vector_repo.delete_by_profile_id(user_db_id=user_db_id, profile_id=201)

    first = user_memory_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=5)
    second = user_memory_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(1), top_k=5)

    assert all(row["profile_id"] != 201 for row in first)
    assert any(row["profile_id"] == 202 for row in second)


def test_replace_all_for_user_rebuilds_index(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    _telegram_id, user_db_id = _create_user(db, telegram_id=666003)

    user_memory_vector_repo.upsert_items(
        user_db_id=user_db_id,
        items=[
            {"profile_id": 301, "kind": "fact", "text": "Старый факт", "vector": _vector(0)},
            {"profile_id": 302, "kind": "fact", "text": "Устаревший факт", "vector": _vector(1)},
        ],
    )

    written = user_memory_vector_repo.replace_all_for_user(
        user_db_id=user_db_id,
        items=[
            {"profile_id": 303, "kind": "fact", "text": "Новый факт", "vector": _vector(2)},
        ],
    )

    assert written == 1
    results = user_memory_vector_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(2),
        top_k=10,
    )
    assert len(results) == 1
    assert results[0]["profile_id"] == 303
