from __future__ import annotations

from handlers import knowledge_commands


def test_doc_status_badges_include_parser_summary_and_structure():
    badges = knowledge_commands._doc_status_badges(
        {
            "parser_backend": "docling",
            "summary_status": "generated",
            "doc_has_tables": True,
            "doc_has_headings": True,
        }
    )

    assert badges == " [docling, summary, tables, sections]"


def test_build_kb_message_shows_doc_badges(monkeypatch):
    monkeypatch.setattr(knowledge_commands, "is_kb_enabled", lambda user_id: True)
    monkeypatch.setattr(
        knowledge_commands.kb_svc,
        "get_documents",
        lambda user_id: [
            {
                "id": 7,
                "name": "camera_manual.pdf",
                "size_bytes": 2048,
                "chunk_count": 15,
                "source_type": "file",
                "parser_backend": "docling",
                "summary_status": "generated",
                "doc_has_tables": True,
                "doc_has_headings": True,
            }
        ],
    )

    text, _kb = knowledge_commands._build_kb_message(user_id=123)

    assert "camera_manual.pdf" in text
    assert "[docling, summary, tables, sections]" in text
