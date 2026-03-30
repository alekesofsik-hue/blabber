from __future__ import annotations

from database import get_connection
from repositories import kb_vector_repo, knowledge_repo, user_repo
from services import document_summary_service
from services import knowledge_service


def _create_user(db, telegram_id: int = 999301) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "reindex_tester", "Reindex", role_id)
    return telegram_id, user["id"]


def _vector(axis: int, dim: int = kb_vector_repo.EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_reindex_document_rebuilds_lancedb_vectors_from_stored_chunks(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "lancedb")
    monkeypatch.setenv("KB_WRITE_LEGACY_EMBEDDING", "false")
    telegram_id, user_db_id = _create_user(db)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(0))

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "ops.txt",
        "Сервер нужно перезапустить перед релизом.".encode(),
    )
    assert ok is True

    docs = knowledge_service.get_documents(telegram_id)
    doc_id = docs[0]["id"]
    assert kb_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(0), top_k=10)

    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(1) for _ in texts])
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_single", lambda query: _vector(1))

    ok, msg = knowledge_service.reindex_document(telegram_id, doc_id)
    assert ok is True
    assert "vector index обновлён" in msg

    results = kb_vector_repo.search_by_vector(user_db_id=user_db_id, query_vector=_vector(1), top_k=10)
    assert results
    chunks = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert all(chunk["embedding"] is None for chunk in chunks)


def test_reindex_document_can_refresh_legacy_blob_when_enabled(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_WRITE_LEGACY_EMBEDDING", "false")
    telegram_id, user_db_id = _create_user(db, telegram_id=999302)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "legacy.txt",
        "Иван Петров директор фирмы.".encode(),
    )
    assert ok is True

    doc_id = knowledge_service.get_documents(telegram_id)[0]["id"]
    chunks = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert all(chunk["embedding"] is None for chunk in chunks)

    monkeypatch.setenv("KB_WRITE_LEGACY_EMBEDDING", "true")
    ok, msg = knowledge_service.reindex_document(telegram_id, doc_id)
    assert ok is True
    assert "legacy BLOB тоже освежён" in msg

    chunks = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert all(chunk["embedding"] is not None for chunk in chunks)


def test_reindex_all_documents_updates_multiple_docs(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_WRITE_LEGACY_EMBEDDING", "false")
    telegram_id, _user_db_id = _create_user(db, telegram_id=999303)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])

    assert knowledge_service.index_document(telegram_id, "one.txt", b"alpha beta gamma")[0] is True
    assert knowledge_service.index_document(telegram_id, "two.txt", b"delta epsilon zeta")[0] is True

    ok, msg = knowledge_service.reindex_all_documents(telegram_id)
    assert ok is True
    assert "Переиндексировано документов: 2/2." in msg


def test_reindex_document_can_refresh_summary_only(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    telegram_id, user_db_id = _create_user(db, telegram_id=999304)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: False)

    ok, _ = knowledge_service.index_document(
        telegram_id,
        "summary.txt",
        "# Camera\n\nThe diaphragm controls light.".encode(),
    )
    assert ok is True

    doc_id = knowledge_service.get_documents(telegram_id)[0]["id"]
    monkeypatch.setattr(
        knowledge_service.doc_summary_svc,
        "generate_summary_artifacts",
        lambda *args, **kwargs: document_summary_service.SummaryArtifacts(
            summary="Документ про диафрагму.",
            key_topics=["диафрагма"],
            suggested_questions=["Как работает диафрагма?"],
            status="generated",
            source="llm",
            generated_at="2026-03-30T12:00:00+00:00",
        ),
    )

    ok, msg = knowledge_service.reindex_document(telegram_id, doc_id, mode="summary")
    assert ok is True
    assert "summary=generated" in msg

    doc = knowledge_service.get_documents(telegram_id)[0]
    assert doc["summary_text"] == "Документ про диафрагму."
    assert doc["summary_status"] == "generated"


def test_reindex_all_documents_dry_run_reports_mode_without_mutation(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    telegram_id, _user_db_id = _create_user(db, telegram_id=999305)

    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "embed_texts", lambda texts: [_vector(0) for _ in texts])

    assert knowledge_service.index_document(telegram_id, "one.txt", b"# One\n\nalpha beta")[0] is True

    before = knowledge_service.get_documents(telegram_id)[0]
    ok, msg = knowledge_service.reindex_all_documents(telegram_id, mode="all", dry_run=True)
    after = knowledge_service.get_documents(telegram_id)[0]

    assert ok is True
    assert "dry-run" in msg
    assert "Режим: all." in msg
    assert before["summary_generated_at"] == after["summary_generated_at"]


def test_inspect_document_and_snapshot_report_operational_status(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    telegram_id, user_db_id = _create_user(db, telegram_id=999306)

    doc_id = knowledge_repo.add_document(
        user_db_id,
        "manual.pdf",
        100,
        1,
        parser_backend="docling",
        parser_mode="docling_with_legacy_fallback",
        source_format="PDF",
        doc_has_tables=True,
        doc_has_headings=True,
        summary_status="generated",
    )
    knowledge_repo.add_chunks(
        doc_id,
        user_db_id,
        ["| ISO | value |\n| --- | --- |\n| 100 | bright |"],
        chunk_metadata=[
            {
                "section_title": "Характеристики",
                "heading_path": ["Характеристики"],
                "page_from": 4,
                "page_to": 4,
                "block_type": "table",
                "is_table": True,
                "table_id": "table_1",
                "meta": {},
            }
        ],
    )

    inspect = knowledge_service.inspect_document(telegram_id, doc_id)
    snapshot = knowledge_service.get_kb_operations_snapshot(telegram_id)

    assert inspect is not None
    assert inspect["parse_success"] is True
    assert inspect["summary_ready"] is True
    assert inspect["metadata_richness"] in {"medium", "high"}
    assert snapshot["documents_total"] == 1
    assert snapshot["docling_docs"] == 1
    assert snapshot["table_docs"] == 1
