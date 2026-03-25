from __future__ import annotations

from database import get_connection
from repositories import user_repo
from services import knowledge_service


def _create_user(db, telegram_id: int = 999201) -> int:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user_repo.create(telegram_id, "url_tester", "URL", role_id)
    return telegram_id


def _vector(axis: int, dim: int = 1536) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_index_url_persists_url_document_and_retrieves(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "lancedb")
    monkeypatch.setenv("KB_ENABLE_URL_INGESTION", "true")

    telegram_id = _create_user(db, 999202)

    monkeypatch.setattr(
        knowledge_service.url_ing_svc,
        "fetch_url_document",
        lambda url: {
            "url": "https://example.com/article",
            "title": "Example Article",
            "text": "Иван Петров директор фирмы",
            "size_bytes": 128,
            "content_type": "text/html",
        },
    )
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(0))

    ok, msg = knowledge_service.index_url(telegram_id, "https://example.com/article")
    assert ok is True
    assert "+ embeddings" in msg

    docs = knowledge_service.get_documents(telegram_id)
    assert len(docs) == 1
    assert docs[0]["name"] == "Example Article"
    assert docs[0]["source_type"] == "url"
    assert docs[0]["source_url"] == "https://example.com/article"

    results = knowledge_service.retrieve_context(telegram_id, "Кто руководит организацией?", top_k=3)
    assert len(results) >= 1
    assert "иван петров" in results[0]["content"].lower()


def test_index_url_respects_feature_flag(db, monkeypatch):
    monkeypatch.setenv("KB_ENABLE_URL_INGESTION", "false")
    telegram_id = _create_user(db, 999203)

    ok, msg = knowledge_service.index_url(telegram_id, "https://example.com/article")
    assert ok is False
    assert "отключен" in msg
