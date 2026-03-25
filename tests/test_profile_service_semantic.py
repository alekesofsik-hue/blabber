from __future__ import annotations

from database import get_connection
from repositories import user_memory_vector_repo, user_repo
from services import profile_service, user_memory_service


def _create_user(db, telegram_id: int = 668001) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "profilesem_tester", "ProfileSem", role_id)
    return telegram_id, user["id"]


def _vector(axis: int = 0, dim: int = user_memory_vector_repo.EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_profile_service_add_fact_uses_semantic_dedup(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("USER_MEMORY_SIMILARITY_THRESHOLD", "0.75")
    telegram_id, user_db_id = _create_user(db)

    emb_map = {
        "Меня зовут Алексей": _vector(0),
        "Я Алексей": [x * 0.8 for x in _vector(0)],
    }
    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(user_memory_service.emb_svc, "embed_single", lambda text: emb_map[text])

    ok_first, msg_first = profile_service.add_fact(telegram_id, "Меня зовут Алексей")
    ok_second, msg_second = profile_service.add_fact(telegram_id, "Я Алексей")

    items = profile_service.get_items_with_ids(telegram_id)
    assert ok_first is True
    assert ok_second is True
    assert "Запомнил" in msg_first
    assert "Похожий факт уже есть" in msg_second
    assert len(items) == 1
    assert items[0]["kind"] == "fact"
    assert items[0]["fact"] == "Меня зовут Алексей"

    results = user_memory_vector_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(0),
        top_k=10,
    )
    assert len(results) == 1


def test_profile_service_delete_fact_removes_vector_index(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, user_db_id = _create_user(db, telegram_id=668002)

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(user_memory_service.emb_svc, "embed_single", lambda text: _vector(0))

    ok, _ = profile_service.add_fact(telegram_id, "Факт для удаления")
    assert ok is True

    items = profile_service.get_items_with_ids(telegram_id)
    assert len(items) == 1
    profile_id = items[0]["id"]
    assert user_memory_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=10)

    deleted, msg = profile_service.delete_fact_by_id(telegram_id, profile_id)
    assert deleted is True
    assert "Забыл" in msg
    assert user_memory_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=10) == []


def test_profile_service_clear_facts_clears_vector_index(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, user_db_id = _create_user(db, telegram_id=668003)

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(
        user_memory_service.emb_svc,
        "embed_single",
        lambda text: _vector(0 if "перв" in text.lower() else 1),
    )

    ok1, _ = profile_service.add_fact(telegram_id, "Первый факт")
    ok2, _ = profile_service.add_fact(telegram_id, "Второй факт")
    assert ok1 is True
    assert ok2 is True
    assert len(profile_service.get_items_with_ids(telegram_id)) == 2

    profile_service.clear_facts(telegram_id)

    assert profile_service.get_items_with_ids(telegram_id) == []
    assert user_memory_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=10) == []
