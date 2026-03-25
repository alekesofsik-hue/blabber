from __future__ import annotations

from database import get_connection
from repositories import profile_repo, user_repo
from services import user_memory_service


def _create_user(db, telegram_id: int = 667001) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "memsvc_tester", "MemSvc", role_id)
    return telegram_id, user["id"]


def _vector(axis: int = 0, dim: int = 1536, value: float = 1.0) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = value
    return vec


def test_save_memory_item_skips_semantic_duplicate(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("USER_MEMORY_SIMILARITY_THRESHOLD", "0.75")
    monkeypatch.setenv("USER_MEMORY_DECISION_MODE", "skip")
    telegram_id, user_db_id = _create_user(db)

    vec_a = _vector(0, value=1.0)
    vec_b = _vector(0, value=0.8)
    emb_map = {
        "Меня зовут Алексей": vec_a,
        "Я Алексей": vec_b,
    }

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(user_memory_service.emb_svc, "embed_single", lambda text: emb_map[text])

    first = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Меня зовут Алексей")
    second = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Я Алексей")

    items = profile_repo.get_items_with_ids(user_db_id)
    assert first["action"] == "inserted"
    assert second["action"] == "skipped"
    assert len(items) == 1


def test_save_memory_item_skips_exact_duplicate(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, user_db_id = _create_user(db, telegram_id=667007)

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: False)

    first = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Меня зовут Алексей")
    second = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Меня зовут Алексей")

    items = profile_repo.get_items_with_ids(user_db_id)
    assert first["action"] == "inserted"
    assert second["action"] == "skipped"
    assert len(items) == 1


def test_save_memory_item_updates_semantic_duplicate_in_update_mode(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("USER_MEMORY_SIMILARITY_THRESHOLD", "0.75")
    monkeypatch.setenv("USER_MEMORY_DECISION_MODE", "update")
    telegram_id, user_db_id = _create_user(db, telegram_id=667002)

    vec_a = _vector(0, value=1.0)
    vec_b = _vector(0, value=0.85)
    emb_map = {
        "Я Алексей": vec_a,
        "Я Алексей и я разработчик Python": vec_b,
    }

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(user_memory_service.emb_svc, "embed_single", lambda text: emb_map[text])

    first = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Я Алексей")
    second = user_memory_service.save_memory_item(
        telegram_id,
        kind="fact",
        text="Я Алексей и я разработчик Python",
    )

    items = profile_repo.get_items_with_ids(user_db_id)
    assert first["action"] == "inserted"
    assert second["action"] == "updated"
    assert len(items) == 1
    assert items[0]["fact"] == "Я Алексей и я разработчик Python"


def test_save_memory_item_inserts_distant_fact(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("USER_MEMORY_SIMILARITY_THRESHOLD", "0.75")
    telegram_id, user_db_id = _create_user(db, telegram_id=667003)

    emb_map = {
        "Меня зовут Алексей": _vector(0),
        "Я люблю кошек": _vector(1),
    }

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(user_memory_service.emb_svc, "embed_single", lambda text: emb_map[text])

    first = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Меня зовут Алексей")
    second = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Я люблю кошек")

    items = profile_repo.get_items_with_ids(user_db_id)
    assert first["action"] == "inserted"
    assert second["action"] == "inserted"
    assert len(items) == 2


def test_save_memory_item_falls_back_without_embeddings(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, user_db_id = _create_user(db, telegram_id=667004)

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: False)

    result = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Факт без эмбеддингов")

    items = profile_repo.get_items_with_ids(user_db_id)
    assert result["action"] == "inserted"
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == "embeddings_unavailable"
    assert len(items) == 1


def test_save_memory_item_falls_back_when_vector_search_fails(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, user_db_id = _create_user(db, telegram_id=667005)

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(user_memory_service.emb_svc, "embed_single", lambda text: _vector(0))

    def _boom(**kwargs):
        raise RuntimeError("search unavailable")

    monkeypatch.setattr(user_memory_service.vector_repo, "search_by_vector", _boom)

    result = user_memory_service.save_memory_item(telegram_id, kind="fact", text="Факт при сбое поиска")

    items = profile_repo.get_items_with_ids(user_db_id)
    assert result["action"] == "inserted"
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == "vector_search_failed"
    assert len(items) == 1


def test_reindex_user_memory_rebuilds_index_from_existing_sqlite_rows(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, user_db_id = _create_user(db, telegram_id=667006)

    first_id = profile_repo.add_item_returning_id(user_db_id, fact="Меня зовут Алексей", kind="fact")
    second_id = profile_repo.add_item_returning_id(user_db_id, fact="Я люблю кошек", kind="fact")
    assert first_id is not None
    assert second_id is not None

    monkeypatch.setattr(user_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(
        user_memory_service.emb_svc,
        "embed_texts",
        lambda texts: [_vector(i) for i, _ in enumerate(texts)],
    )

    result = user_memory_service.reindex_user_memory(telegram_id)

    search = user_memory_service.vector_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(0),
        top_k=10,
    )
    assert result["ok"] is True
    assert result["indexed"] == 2
    assert {row["profile_id"] for row in search} == {first_id, second_id}
