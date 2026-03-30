from __future__ import annotations

from database import get_connection
from repositories import knowledge_repo, kb_vector_repo, user_repo
from services import knowledge_service


def _create_user(db, telegram_id: int = 999201) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "structured_retrieval", "Structured Retrieval", role_id)
    return telegram_id, user["id"]


def _vector(axis: int, dim: int = kb_vector_repo.EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_structured_retrieval_boosts_matching_section_titles(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "sqlite")
    telegram_id, user_db_id = _create_user(db, telegram_id=999202)

    doc_id = knowledge_repo.add_document(user_db_id, "manual.pdf", 100, 2, parser_backend="docling")
    chunk_uids = knowledge_repo.add_chunks(
        doc_id,
        user_db_id,
        [
            "Настройка выдержки и света.",
            "Объектив влияет на угол обзора.",
        ],
        embeddings=None,
        chunk_metadata=[
            {"section_title": "Экспозиция", "heading_path": ["Экспозиция"], "block_type": "prose", "is_table": False, "meta": {}},
            {"section_title": "Объектив", "heading_path": ["Объектив"], "block_type": "prose", "is_table": False, "meta": {}},
        ],
    )
    assert chunk_uids

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_structured_retrieval_enabled", lambda: True)

    results = knowledge_service.retrieve_context(telegram_id, "Что сказано про объектив?", top_k=2)

    assert results
    assert results[0]["section_title"] == "Объектив"


def test_structured_retrieval_prefers_table_chunks_for_table_like_queries(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "sqlite")
    telegram_id, user_db_id = _create_user(db, telegram_id=999203)

    doc_id = knowledge_repo.add_document(user_db_id, "specs.pdf", 100, 2, parser_backend="docling")
    knowledge_repo.add_chunks(
        doc_id,
        user_db_id,
        [
            "Камера подходит для путешествий.",
            "| ISO | значение |\n| --- | --- |\n| 100 | bright |\n| 800 | dark |",
        ],
        embeddings=None,
        chunk_metadata=[
            {"section_title": "Описание", "heading_path": ["Описание"], "block_type": "prose", "is_table": False, "meta": {}},
            {"section_title": "Характеристики", "heading_path": ["Характеристики"], "block_type": "table", "is_table": True, "table_id": "table_1", "meta": {}},
        ],
    )

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_structured_retrieval_enabled", lambda: True)

    results = knowledge_service.retrieve_context(telegram_id, "Какие значения ISO в таблице?", top_k=2)

    assert results
    assert results[0]["is_table"] is True


def test_build_kb_context_includes_provenance_for_structured_chunks(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "sqlite")
    telegram_id, user_db_id = _create_user(db, telegram_id=999204)

    doc_id = knowledge_repo.add_document(user_db_id, "manual.pdf", 100, 1, parser_backend="docling")
    knowledge_repo.add_chunks(
        doc_id,
        user_db_id,
        ["| ISO | значение |\n| --- | --- |\n| 100 | bright |"],
        embeddings=None,
        chunk_metadata=[
            {
                "section_title": "Характеристики",
                "heading_path": ["Характеристики"],
                "page_from": 7,
                "page_to": 7,
                "block_type": "table",
                "is_table": True,
                "table_id": "table_1",
                "meta": {},
            }
        ],
    )

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_structured_retrieval_enabled", lambda: True)

    payload = knowledge_service.build_kb_context_payload(telegram_id, "Покажи таблицу характеристик")

    assert payload["used_kb"] is True
    assert "Раздел: Характеристики" in payload["context"]
    assert "Стр.: 7" in payload["context"]
    assert "Таблица" in payload["context"]


def test_structured_retrieval_keeps_working_without_metadata(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "sqlite")
    telegram_id, user_db_id = _create_user(db, telegram_id=999205)

    doc_id = knowledge_repo.add_document(user_db_id, "plain.txt", 100, 1)
    knowledge_repo.add_chunks(doc_id, user_db_id, ["Сервер перезапускается через systemctl restart blabber"])

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_structured_retrieval_enabled", lambda: True)

    results = knowledge_service.retrieve_context(telegram_id, "Как перезапустить сервер?", top_k=2)

    assert results
    assert "systemctl" in results[0]["content"].lower()
