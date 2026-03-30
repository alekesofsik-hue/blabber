from __future__ import annotations

from services import knowledge_service


def test_build_kb_context_payload_when_no_results(monkeypatch):
    monkeypatch.setattr(knowledge_service, "retrieve_context", lambda telegram_id, query: [])

    payload = knowledge_service.build_kb_context_payload(777, "Как работает диафрагма?")

    assert payload["context"] is None
    assert payload["results_count"] == 0
    assert payload["source_docs"] == []
    assert payload["source_refs"] == []
    assert payload["used_kb"] is False


def test_build_kb_context_payload_collects_unique_sources(monkeypatch):
    monkeypatch.setattr(
        knowledge_service,
        "retrieve_context",
        lambda telegram_id, query: [
            {
                "content": "Фрагмент 1 про выдержку и устойчивую съёмку.",
                "doc_name": "NX500_rules.pdf",
                "score": 0.9,
                "section_title": "Съёмка с рук",
                "page_from": 12,
                "page_to": 12,
                "is_table": False,
                "block_type": "prose",
            },
            {
                "content": "Фрагмент 2 про выдержку и устойчивую съёмку.",
                "doc_name": "NX500_rules.pdf",
                "score": 0.8,
                "section_title": "Съёмка с рук",
                "page_from": 12,
                "page_to": 12,
                "is_table": False,
                "block_type": "prose",
            },
            {
                "content": "Фрагмент 3 про стабилизацию.",
                "doc_name": "Manual.pdf",
                "score": 0.7,
                "section_title": "Стабилизация",
                "page_from": 4,
                "page_to": 5,
                "is_table": False,
                "block_type": "prose",
            },
        ],
    )

    payload = knowledge_service.build_kb_context_payload(777, "Как работает диафрагма?")

    assert payload["used_kb"] is True
    assert payload["results_count"] == 3
    assert payload["source_docs"] == ["NX500_rules.pdf", "Manual.pdf"]
    assert len(payload["source_refs"]) == 2
    assert payload["source_refs"][0]["section_title"] == "Съёмка с рук"
    assert payload["source_refs"][0]["page_from"] == 12
    assert "Фрагмент 1" in payload["source_refs"][0]["preview"]
    assert payload["context"].startswith("[Факты из базы знаний]")
