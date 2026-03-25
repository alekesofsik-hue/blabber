from __future__ import annotations

from database import get_connection
from repositories import user_repo
from services import knowledge_service


def _create_user(db, telegram_id: int = 999100) -> int:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user_repo.create(telegram_id, "retrieval_tester", "Retrieval", role_id)
    return telegram_id


def _vector(axis: int, dim: int = 1536) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def _embed_texts_by_content(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for text in texts:
        lowered = text.lower()
        if "директор" in lowered or "фирмы" in lowered:
            vectors.append(_vector(0))
        elif "сервер" in lowered or "deployment" in lowered:
            vectors.append(_vector(1))
        else:
            vectors.append(_vector(2))
    return vectors


def test_lancedb_backend_retrieves_exact_match(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "lancedb")

    telegram_id = _create_user(db, 999101)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", _embed_texts_by_content)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(1))

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "deploy.txt",
        "Deployment guide: сервер нужно перезапустить перед релизом.".encode(),
    )
    assert ok is True

    results = knowledge_service.retrieve_context(telegram_id, "Как перезапустить сервер?", top_k=3)
    assert len(results) >= 1
    assert "сервер" in results[0]["content"].lower()


def test_lancedb_backend_handles_synonym_query_without_bm25_overlap(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "lancedb")

    telegram_id = _create_user(db, 999102)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", _embed_texts_by_content)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(0))

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "org.txt",
        "Иван Петров директор фирмы".encode(),
    )
    assert ok is True

    # Вопрос не содержит общих токенов с фрагментом, кроме семантики.
    results = knowledge_service.retrieve_context(telegram_id, "Кто руководит организацией?", top_k=3)
    assert len(results) >= 1
    assert "иван петров" in results[0]["content"].lower()


def test_lancedb_backend_falls_back_to_bm25_when_vectors_absent(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "lancedb")

    telegram_id = _create_user(db, 999103)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: False)

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "plain.txt",
        "Сервер запускается командой systemctl restart blabber".encode(),
    )
    assert ok is True

    results = knowledge_service.retrieve_context(telegram_id, "Как перезапустить blabber?", top_k=3)
    assert len(results) >= 1
    assert any(row["doc_name"] == "plain.txt" for row in results)
    assert any("blabber" in row["content"].lower() or "systemctl" in row["content"].lower() for row in results)


def test_lancedb_backend_falls_back_when_search_errors(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "lancedb")

    telegram_id = _create_user(db, 999104)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", _embed_texts_by_content)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(1))

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "fallback.txt",
        "Сервер перезапускается через systemctl restart blabber".encode(),
    )
    assert ok is True

    def _boom(*args, **kwargs):
        raise RuntimeError("vector search failed")

    monkeypatch.setattr(knowledge_service.kb_vector_repo, "search_by_vector", _boom)
    results = knowledge_service.retrieve_context(telegram_id, "Как перезапустить сервер?", top_k=3)
    assert len(results) >= 1
    assert "systemctl" in results[0]["content"].lower()


def test_lancedb_backend_handles_multiple_documents_and_top_k(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "lancedb")

    telegram_id = _create_user(db, 999105)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", _embed_texts_by_content)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(1))

    assert knowledge_service.index_document(
        telegram_id,
        "deploy.txt",
        "Deployment guide: сервер нужно перезапустить перед релизом.".encode(),
    )[0] is True
    assert knowledge_service.index_document(
        telegram_id,
        "org.txt",
        "Иван Петров директор фирмы".encode(),
    )[0] is True

    results = knowledge_service.retrieve_context(telegram_id, "Что делать с сервером перед релизом?", top_k=2)
    assert len(results) <= 2
    assert any(row["doc_name"] == "deploy.txt" for row in results)


def test_hybrid_migration_backend_returns_new_results(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "hybrid_migration")

    telegram_id = _create_user(db, 999106)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", _embed_texts_by_content)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(0))

    assert knowledge_service.index_document(
        telegram_id,
        "org.txt",
        "Иван Петров директор фирмы".encode(),
    )[0] is True

    results = knowledge_service.retrieve_context(telegram_id, "Кто руководит организацией?", top_k=3)
    assert len(results) >= 1
    assert "иван петров" in results[0]["content"].lower()


def test_lancedb_backend_can_shadow_compare_without_hybrid_mode(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "lancedb")
    monkeypatch.setenv("KB_ENABLE_SHADOW_COMPARE", "true")

    telegram_id = _create_user(db, 999107)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", _embed_texts_by_content)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(0))

    shadow_calls: list[tuple[str, list[dict], list[dict]]] = []

    def _capture_shadow_compare(*, telegram_id, old_results, new_results, mode="hybrid_migration"):
        shadow_calls.append((mode, old_results, new_results))

    monkeypatch.setattr(knowledge_service, "_log_shadow_compare", _capture_shadow_compare)

    assert knowledge_service.index_document(
        telegram_id,
        "org.txt",
        "Иван Петров директор фирмы".encode(),
    )[0] is True

    results = knowledge_service.retrieve_context(telegram_id, "Кто руководит организацией?", top_k=3)
    assert len(results) >= 1
    assert shadow_calls
    assert shadow_calls[0][0] == "shadow_compare"
