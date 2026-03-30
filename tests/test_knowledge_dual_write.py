from __future__ import annotations

from database import get_connection
from repositories import kb_vector_repo, knowledge_repo, user_repo
from services import context_service
from services import knowledge_service


def _create_user(db, telegram_id: int = 888001) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "dualwrite_tester", "DualWrite", role_id)
    return telegram_id, user["id"]


def _vector(axis: int = 0, dim: int = kb_vector_repo.EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_index_document_dual_writes_to_sqlite_and_lancedb(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_WRITE_LEGACY_EMBEDDING", "true")
    telegram_id, user_db_id = _create_user(db)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(
        knowledge_service.emb_svc,
        "embed_texts",
        lambda texts: [_vector(i) for i, _ in enumerate(texts)],
    )

    ok, msg = knowledge_service.index_document(
        telegram_id,
        "dualwrite.txt",
        b"alpha sentence. beta sentence. gamma sentence.",
    )

    assert ok is True
    assert "+ embeddings" in msg

    docs = knowledge_service.get_documents(telegram_id)
    assert len(docs) == 1
    doc_id = docs[0]["id"]

    chunks = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert len(chunks) >= 1
    assert all(chunk["chunk_uid"] for chunk in chunks)
    assert all(chunk["embedding"] is not None for chunk in chunks)

    results = kb_vector_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(0),
        top_k=10,
    )
    assert len(results) >= 1
    assert {row["chunk_uid"] for row in results}.issubset({chunk["chunk_uid"] for chunk in chunks})


def test_index_document_without_embeddings_stays_bm25_only(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    telegram_id, user_db_id = _create_user(db, telegram_id=888002)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: False)

    ok, msg = knowledge_service.index_document(
        telegram_id,
        "bm25_only.txt",
        b"some plain text without embeddings",
    )

    assert ok is True
    assert "BM25-only" in msg

    docs = knowledge_service.get_documents(telegram_id)
    doc_id = docs[0]["id"]
    chunks = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert len(chunks) >= 1
    assert all(chunk["embedding"] is None for chunk in chunks)
    assert kb_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=10) == []


def test_index_document_reports_embedding_failure_honestly(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    telegram_id, user_db_id = _create_user(db, telegram_id=888008)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: None)

    ok, msg = knowledge_service.index_document(
        telegram_id,
        "embed_fail.txt",
        b"some plain text with failed embeddings",
    )

    assert ok is True
    assert "embedding request failed" in msg

    docs = knowledge_service.get_documents(telegram_id)
    doc_id = docs[0]["id"]
    chunks = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert len(chunks) >= 1
    assert all(chunk["embedding"] is None for chunk in chunks)
    assert kb_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=10) == []


def test_lancedb_write_failure_does_not_break_indexing(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_WRITE_LEGACY_EMBEDDING", "true")
    telegram_id, user_db_id = _create_user(db, telegram_id=888003)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])

    def _boom(**kwargs):
        raise RuntimeError("lancedb unavailable")

    monkeypatch.setattr(knowledge_service.kb_vector_repo, "upsert_chunks", _boom)

    ok, msg = knowledge_service.index_document(
        telegram_id,
        "soft_fail.txt",
        b"alpha beta gamma",
    )

    assert ok is True
    assert "+ embeddings" in msg

    docs = knowledge_service.get_documents(telegram_id)
    assert len(docs) == 1
    doc_id = docs[0]["id"]
    chunks = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert len(chunks) >= 1
    assert all(chunk["embedding"] is not None for chunk in chunks)


def test_index_document_defaults_to_lancedb_only_without_legacy_blob_write(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.delenv("KB_WRITE_LEGACY_EMBEDDING", raising=False)
    telegram_id, user_db_id = _create_user(db, telegram_id=888007)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(
        knowledge_service.emb_svc,
        "embed_texts",
        lambda texts: [_vector(i) for i, _ in enumerate(texts)],
    )

    ok, msg = knowledge_service.index_document(
        telegram_id,
        "lancedb_only.txt",
        b"alpha sentence. beta sentence. gamma sentence.",
    )

    assert ok is True
    assert "+ embeddings" in msg

    docs = knowledge_service.get_documents(telegram_id)
    doc_id = docs[0]["id"]
    chunks = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert len(chunks) >= 1
    assert all(chunk["embedding"] is None for chunk in chunks)
    assert kb_vector_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(0),
        top_k=10,
    )


def test_delete_document_cleans_vector_entries(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    telegram_id, user_db_id = _create_user(db, telegram_id=888004)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "cleanup.txt",
        b"alpha beta gamma delta",
    )
    assert ok is True

    docs = knowledge_service.get_documents(telegram_id)
    doc_id = docs[0]["id"]
    assert kb_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=10)

    deleted, msg = knowledge_service.delete_document(telegram_id, doc_id)
    assert deleted is True
    assert "Контекст чата очищен" in msg
    assert kb_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=10) == []


def test_delete_document_clears_chat_context_to_prevent_ghost_answers(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    telegram_id, _user_db_id = _create_user(db, telegram_id=888005)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "ghost.txt",
        b"alpha beta gamma delta",
    )
    assert ok is True

    context_service.add_turn(
        telegram_id,
        "Кто директор компании?",
        "В документе сказано, что директор компании Иван Петров.",
    )
    assert context_service.get_history(telegram_id) != []

    doc_id = knowledge_service.get_documents(telegram_id)[0]["id"]
    deleted, _ = knowledge_service.delete_document(telegram_id, doc_id)
    assert deleted is True
    assert context_service.get_history(telegram_id) == []
    assert context_service.get_summary(telegram_id) is None


def test_clear_all_clears_chat_context_to_prevent_ghost_answers(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    telegram_id, _user_db_id = _create_user(db, telegram_id=888006)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "ghost_clear.txt",
        b"alpha beta gamma delta",
    )
    assert ok is True

    context_service.add_turn(
        telegram_id,
        "Напомни про документ",
        "В документе был важный факт про Ивана Петрова.",
    )
    assert context_service.get_history(telegram_id) != []

    knowledge_service.clear_all(telegram_id)
    assert context_service.get_history(telegram_id) == []
    assert context_service.get_summary(telegram_id) is None
