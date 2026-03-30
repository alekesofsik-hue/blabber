from __future__ import annotations

from database import get_connection
from repositories import knowledge_repo, user_repo
from services import knowledge_service
from services import docling_service


def _create_user(telegram_id: int = 999401) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, f"rollback_{telegram_id}", "Rollback", role_id)
    return telegram_id, user["id"]


def test_disabling_docling_rolls_indexing_back_to_legacy_path(db, monkeypatch):
    telegram_id, _user_db_id = _create_user()

    monkeypatch.setattr(knowledge_service.kb_rollout, "get_doc_parser_mode", lambda: "legacy_only")
    monkeypatch.setattr(knowledge_service.emb_svc, "is_available", lambda: False)

    ok, _msg = knowledge_service.index_document(
        telegram_id,
        "plain.txt",
        b"legacy path document",
    )

    assert ok is True
    doc = knowledge_service.get_documents(telegram_id)[0]
    assert doc["parser_backend"] == "legacy"
    assert doc["parser_mode"] == "legacy_only"


def test_disabling_summary_generation_skips_summary_stage(db, monkeypatch):
    telegram_id, _user_db_id = _create_user(telegram_id=999402)

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_doc_summary_enabled", lambda: False)
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
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("summary must not run")),
    )

    ok, msg = knowledge_service.index_document(
        telegram_id,
        "camera_manual.pdf",
        b"%PDF-demo",
    )

    assert ok is True
    assert "Краткое резюме" not in msg
    doc = knowledge_service.get_documents(telegram_id)[0]
    assert doc["summary_status"] == "pending"
    assert doc["summary_text"] is None


def test_disabling_structured_retrieval_keeps_plain_retrieval_working(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    monkeypatch.setenv("KB_ENABLE_DUAL_WRITE", "true")
    monkeypatch.setenv("KB_VECTOR_BACKEND", "sqlite")
    telegram_id, user_db_id = _create_user(telegram_id=999403)

    doc_id = knowledge_repo.add_document(user_db_id, "manual.pdf", 100, 2, parser_backend="docling")
    knowledge_repo.add_chunks(
        doc_id,
        user_db_id,
        [
            "Объектив влияет на угол обзора.",
            "| ISO | значение |\n| --- | --- |\n| 100 | bright |",
        ],
        chunk_metadata=[
            {"section_title": "Объектив", "heading_path": ["Объектив"], "block_type": "prose", "is_table": False, "meta": {}},
            {"section_title": "Характеристики", "heading_path": ["Характеристики"], "block_type": "table", "is_table": True, "table_id": "table_1", "meta": {}},
        ],
    )

    monkeypatch.setattr(knowledge_service.kb_rollout, "is_structured_retrieval_enabled", lambda: False)

    results = knowledge_service.retrieve_context(telegram_id, "Что сказано про объектив?", top_k=2)

    assert results
    assert "объектив" in results[0]["content"].lower()
