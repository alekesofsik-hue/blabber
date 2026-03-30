from __future__ import annotations

import sqlite3

from database import get_connection
from repositories import knowledge_repo, user_repo
from services import document_summary_service
from services import knowledge_service
from services import docling_service


def _create_user(telegram_id: int = 889001) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, f"user_{telegram_id}", "Structured", role_id)
    return telegram_id, user["id"]


def test_structured_metadata_columns_exist(db):
    conn = sqlite3.connect(str(db))
    document_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(kb_documents)").fetchall()
    }
    chunk_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(kb_chunks)").fetchall()
    }
    conn.close()

    assert {
        "parser_backend",
        "parser_mode",
        "parser_version",
        "source_format",
        "doc_structure_json",
        "doc_metadata_json",
        "doc_has_tables",
        "doc_has_headings",
        "doc_page_count",
        "summary_text",
        "summary_topics_json",
        "summary_questions_json",
        "summary_status",
        "summary_generated_at",
        "summary_error",
    }.issubset(document_columns)
    assert {
        "section_title",
        "heading_path_json",
        "page_from",
        "page_to",
        "block_type",
        "is_table",
        "table_id",
        "meta_json",
    }.issubset(chunk_columns)


def test_repository_defaults_keep_backward_compatible_reads(db):
    _telegram_id, user_db_id = _create_user()

    doc_id = knowledge_repo.add_document(
        user_db_id,
        "legacy-compatible.txt",
        42,
        1,
    )
    chunk_uids = knowledge_repo.add_chunks(doc_id, user_db_id, ["plain chunk"])

    doc = knowledge_repo.get_document(doc_id, user_db_id)
    chunks = knowledge_repo.get_chunks_by_uids(user_db_id, chunk_uids)

    assert doc is not None
    assert doc["parser_backend"] is None
    assert doc["doc_has_tables"] is False
    assert doc["doc_has_headings"] is False
    assert doc["doc_structure_json"] is None
    assert doc["summary_status"] == "pending"

    assert len(chunks) == 1
    assert chunks[0]["section_title"] is None
    assert chunks[0]["heading_path_json"] is None
    assert chunks[0]["is_table"] is False
    assert chunks[0]["meta_json"] is None


def test_index_document_persists_structured_metadata(db, monkeypatch):
    telegram_id, user_db_id = _create_user(telegram_id=889002)

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_docling_structured_chunks_enabled", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: False)
    monkeypatch.setattr(
        knowledge_service.docling_svc,
        "parse_document",
        lambda filename, data, parser_mode=None: docling_service.ParsedDocument(
            filename=filename,
            text="# Camera\n\nThe diaphragm controls light.\n\n| f-stop | effect |\n| --- | --- |\n| 2.8 | blur |\n",
            parser_backend="docling",
            parser_mode="docling_with_legacy_fallback",
            parser_version="2.82.0",
            source_format="PDF",
            page_count=3,
            has_tables=True,
            has_headings=True,
            structure={"headings": ["Camera"]},
            warnings=["demo warning"],
            metadata={"docling_status": "SUCCESS"},
        ),
    )

    ok, _msg = knowledge_service.index_document(
        telegram_id,
        "camera_manual.pdf",
        b"%PDF-demo",
    )

    assert ok is True

    docs = knowledge_service.get_documents(telegram_id)
    assert len(docs) == 1
    doc = docs[0]
    assert doc["parser_backend"] == "docling"
    assert doc["parser_mode"] == "docling_with_legacy_fallback"
    assert doc["parser_version"] == "2.82.0"
    assert doc["source_format"] == "PDF"
    assert doc["doc_has_tables"] is True
    assert doc["doc_has_headings"] is True
    assert doc["doc_page_count"] == 3
    assert doc["doc_structure_json"] == {"headings": ["Camera"]}
    assert doc["doc_metadata_json"]["docling_status"] == "SUCCESS"
    assert doc["doc_metadata_json"]["warnings"] == ["demo warning"]
    assert doc["doc_metadata_json"]["pipeline_mode"] == "structured_docling"
    assert doc["doc_metadata_json"]["normalized_block_count"] >= 2
    assert doc["summary_status"] == "pending"

    chunks = knowledge_repo.get_all_chunks(user_db_id)
    assert len(chunks) >= 1
    assert chunks[0]["block_type"] in {"prose", "table", "markdown"}
    assert chunks[0]["meta_json"]["parser_backend"] == "docling"
    assert isinstance(chunks[0]["meta_json"]["char_count"], int)
    assert isinstance(chunks[0]["meta_json"]["token_estimate"], int)
    assert any(chunk["is_table"] for chunk in chunks)


def test_index_document_falls_back_to_legacy_chunking_on_structured_builder_failure(db, monkeypatch):
    telegram_id, user_db_id = _create_user(telegram_id=889003)

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_docling_structured_chunks_enabled", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: False)
    monkeypatch.setattr(
        knowledge_service.docling_svc,
        "parse_document",
        lambda filename, data, parser_mode=None: docling_service.ParsedDocument(
            filename=filename,
            text="# Camera\n\nThe diaphragm controls light.",
            parser_backend="docling",
            parser_mode="docling_with_legacy_fallback",
            parser_version="2.82.0",
            source_format="PDF",
            has_headings=True,
            structure={"headings": ["Camera"]},
            metadata={"docling_status": "SUCCESS"},
        ),
    )
    monkeypatch.setattr(
        knowledge_service.kb_ingest_svc,
        "build_chunks",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("chunk builder exploded")),
    )

    ok, _msg = knowledge_service.index_document(
        telegram_id,
        "camera_manual.pdf",
        b"%PDF-demo",
    )

    assert ok is True
    doc = knowledge_service.get_documents(telegram_id)[0]
    assert doc["doc_metadata_json"]["pipeline_mode"] == "legacy_chunk_text"
    assert doc["doc_metadata_json"]["chunking_fallback_used"] is True
    assert "chunk builder exploded" in doc["doc_metadata_json"]["chunking_fallback_reason"]

    chunks = knowledge_repo.get_all_chunks(user_db_id)
    assert len(chunks) >= 1
    assert chunks[0]["meta_json"]["parser_backend"] == "docling"


def test_index_document_generates_and_saves_summary_artifacts(db, monkeypatch):
    telegram_id, user_db_id = _create_user(telegram_id=889004)

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_docling_structured_chunks_enabled", lambda: True)
    monkeypatch.setattr(knowledge_service.kb_rollout, "is_doc_summary_enabled", lambda: True)
    monkeypatch.setattr(knowledge_service.kb_rollout, "is_doc_summary_save_enabled", lambda: True)
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: False)
    monkeypatch.setattr(
        knowledge_service.docling_svc,
        "parse_document",
        lambda filename, data, parser_mode=None: docling_service.ParsedDocument(
            filename=filename,
            text="# Camera\n\nThe diaphragm controls light.\n",
            parser_backend="docling",
            parser_mode="docling_with_legacy_fallback",
            parser_version="2.82.0",
            source_format="PDF",
            has_headings=True,
            structure={"headings": ["Camera"]},
            metadata={"docling_status": "SUCCESS"},
        ),
    )
    monkeypatch.setattr(
        knowledge_service.doc_summary_svc,
        "generate_summary_artifacts",
        lambda *args, **kwargs: document_summary_service.SummaryArtifacts(
            summary="Документ объясняет работу диафрагмы.",
            key_topics=["диафрагма", "экспозиция"],
            suggested_questions=["Как работает диафрагма?"],
            warnings=[],
            status="generated",
            source="llm",
            model="openrouter",
            generated_at="2026-03-30T10:00:00+00:00",
        ),
    )

    ok, msg = knowledge_service.index_document(
        telegram_id,
        "camera_manual.pdf",
        b"%PDF-demo",
    )

    assert ok is True
    assert "Краткое резюме" in msg
    assert "Как работает диафрагма?" in msg

    docs = knowledge_service.get_documents(telegram_id)
    assert len(docs) == 1
    doc = docs[0]
    assert doc["summary_status"] == "generated"
    assert doc["summary_text"] == "Документ объясняет работу диафрагмы."
    assert doc["summary_topics_json"] == ["диафрагма", "экспозиция"]
    assert doc["summary_questions_json"] == ["Как работает диафрагма?"]
    assert doc["summary_generated_at"] == "2026-03-30T10:00:00+00:00"
    assert doc["summary_error"] is None
