from __future__ import annotations

from handlers import history_day_commands


def test_resolve_image_request_accepts_explicit_date():
    result = history_day_commands._resolve_image_request("03-27", "")

    assert result["mode"] == "date"
    assert result["date"] == "03-27"
    assert result["image_question"] == ""
    assert result["error"] == ""


def test_resolve_image_request_uses_latest_context_for_question():
    result = history_day_commands._resolve_image_request(
        "Что на нем показано?",
        "03-27",
    )

    assert result["mode"] == "question"
    assert result["date"] == "03-27"
    assert result["image_question"] == "Что на нем показано?"
    assert result["error"] == ""


def test_resolve_image_request_reports_missing_context_for_question():
    result = history_day_commands._resolve_image_request(
        "Какого цвета объект на изображении?",
        "",
    )

    assert result["mode"] == "question_missing_context"
    assert result["date"] == ""
    assert "Сначала нужно получить факт дня" in result["error"]


def test_build_memory_snapshot_text_renders_recent_memory(monkeypatch):
    monkeypatch.setattr(
        history_day_commands,
        "get_history_day_memory_snapshot",
        lambda user_id, limit=8: {
            "ok": True,
            "memory_available": True,
            "latest_event_date": "03-27",
            "saved_messages_count": 2,
            "items": [
                {
                    "scenario_tag": "history_day_image",
                    "event_date": "03-27",
                    "created_at": "2026-03-27 12:00:00",
                    "text": "Покажи изображение по факту дня",
                },
                {
                    "scenario_tag": "history_day_fact",
                    "event_date": "03-27",
                    "created_at": "2026-03-27 11:59:00",
                    "text": "Что произошло сегодня в истории?",
                },
            ],
        },
    )

    text = history_day_commands._build_memory_snapshot_text(777300)

    assert "Память сценария" in text
    assert "03-27" in text
    assert "Изображение и анализ" in text
    assert "Что произошло сегодня в истории?" in text
