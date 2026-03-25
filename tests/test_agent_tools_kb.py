from __future__ import annotations

from services import agent_tools


def test_fetch_summary_reuses_shared_url_ingestion(monkeypatch):
    monkeypatch.setattr(
        agent_tools.url_ing_svc,
        "fetch_url_document",
        lambda url: {
            "url": "https://example.com/final",
            "title": "Example Title",
            "text": "A" * 20,
            "size_bytes": 128,
            "content_type": "text/html",
        },
    )

    result = agent_tools.fetch_summary("https://example.com/start", max_chars=10)
    assert result["url"] == "https://example.com/final"
    assert result["title"] == "Example Title"
    assert result["text"] == "A" * 10
    assert result["truncated"] is True


def test_save_url_to_kb_for_user_auto_enables_kb(monkeypatch):
    monkeypatch.setattr(
        "services.knowledge_service.index_url",
        lambda user_id, url: (True, "Проиндексировано 3 фрагментов + embeddings"),
    )
    monkeypatch.setattr(agent_tools, "is_kb_enabled", lambda user_id: False)
    enabled_calls: list[tuple[int, bool]] = []
    monkeypatch.setattr(agent_tools, "set_kb_enabled", lambda user_id, value: enabled_calls.append((user_id, value)))

    result = agent_tools.save_url_to_kb_for_user(777, "https://example.com/article")
    assert result["ok"] is True
    assert result["kb_auto_enabled"] is True
    assert enabled_calls == [(777, True)]


def test_save_url_to_kb_uses_active_agent_context(monkeypatch):
    calls: list[tuple[int, str]] = []
    monkeypatch.setattr(
        agent_tools,
        "save_url_to_kb_for_user",
        lambda user_id, url: calls.append((user_id, url)) or {"ok": True, "message": "saved", "url": url},
    )

    token = agent_tools.set_active_agent_user_id(4242)
    try:
        result = agent_tools.save_url_to_kb("https://example.com/article")
    finally:
        agent_tools.reset_active_agent_user_id(token)

    assert result["ok"] is True
    assert calls == [(4242, "https://example.com/article")]
