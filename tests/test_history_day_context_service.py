from __future__ import annotations

from services import history_day_context_service


def test_retrieve_saved_context_combines_tags_sorts_and_deduplicates(monkeypatch):
    monkeypatch.setattr(history_day_context_service.memory_svc, "is_memory_search_available", lambda: True)
    monkeypatch.setattr(
        history_day_context_service.memory_svc,
        "list_saved_messages",
        lambda telegram_id, *, scenario_tag=None, limit=10: [{"source_id": "seed"}],
    )
    responses = {
        "history_day_fact": [
            {
                "source_id": "a1",
                "text": "Мы обсуждали факт о 26 марта и важное историческое событие.",
                "scenario_tag": "history_day_fact",
                "event_date": "03-26",
                "created_at": "2026-03-26 10:00:00",
                "score": 0.91,
            }
        ],
        "history_day_image": [
            {
                "source_id": "a1",
                "text": "Дубликат того же сообщения из другого результата.",
                "scenario_tag": "history_day_fact",
                "event_date": "03-26",
                "created_at": "2026-03-26 10:00:01",
                "score": 0.89,
            },
            {
                "source_id": "b2",
                "text": "Потом показывали изображение моста и его анализ.",
                "scenario_tag": "history_day_image",
                "event_date": "03-26",
                "created_at": "2026-03-26 10:05:00",
                "score": 0.83,
            },
        ],
    }

    def _fake_search(telegram_id: int, *, query: str, scenario_tag: str | None = None, top_k: int = 5):
        assert telegram_id == 777100
        assert query == "О чем ты мне только что рассказывал?"
        return responses.get(scenario_tag or "", [])

    monkeypatch.setattr(history_day_context_service.memory_svc, "search_relevant_messages", _fake_search)
    result = history_day_context_service.retrieve_saved_context(
        777100,
        query="О чем ты мне только что рассказывал?",
    )

    assert result["ok"] is True
    assert result["found_count"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["source_id"] == "a1"
    assert result["items"][1]["source_id"] == "b2"
    assert "[Saved Context From LanceDB]" in result["context_block"]
    assert "history_day_fact" in result["context_block"]
    assert result["fallback_used"] is False


def test_retrieve_saved_context_returns_empty_payload_when_nothing_found(monkeypatch):
    monkeypatch.setattr(history_day_context_service.memory_svc, "is_memory_search_available", lambda: True)
    monkeypatch.setattr(
        history_day_context_service.memory_svc,
        "list_saved_messages",
        lambda telegram_id, *, scenario_tag=None, limit=10: [{"source_id": "seed"}],
    )
    monkeypatch.setattr(
        history_day_context_service.memory_svc,
        "search_relevant_messages",
        lambda telegram_id, *, query, scenario_tag=None, top_k=5: [],
    )

    result = history_day_context_service.retrieve_saved_context(
        777101,
        query="С каким годом это связано?",
    )

    assert result["ok"] is True
    assert result["items"] == []
    assert result["context_block"] == ""
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == "no_matches"


def test_retrieve_saved_context_reports_embeddings_unavailable(monkeypatch):
    monkeypatch.setattr(history_day_context_service.memory_svc, "is_memory_search_available", lambda: False)

    result = history_day_context_service.retrieve_saved_context(
        777102,
        query="О чем ты мне только что рассказывал?",
    )

    assert result["items"] == []
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == "embeddings_unavailable"


def test_format_saved_context_block_limits_noise():
    block = history_day_context_service.format_saved_context_block(
        [
            {
                "source_id": "x1",
                "text": "Очень длинное сообщение " * 40,
                "scenario_tag": "history_day_fact",
                "event_date": "03-26",
                "created_at": "2026-03-26 10:00:00",
                "score": 0.95,
            }
        ]
    )

    assert "[Saved Context From LanceDB]" in block
    assert "score=0.950" in block
    assert len(block) <= history_day_context_service.MAX_CONTEXT_BLOCK_CHARS
