from __future__ import annotations

from services import history_day_orchestrator


def test_run_fact_scenario_formats_success(monkeypatch):
    monkeypatch.setattr(history_day_orchestrator, "_translate_to_russian", lambda text, telegram_id: text)
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_fact_of_the_day_user_message",
        lambda telegram_id, *, user_message, date="": {"action": "saved"},
    )
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_fact_of_the_day_registry",
        lambda: object(),
    )
    monkeypatch.setattr(
        history_day_orchestrator,
        "_invoke_tool",
        lambda registry, tool_name, arguments: {
            "ok": True,
            "date": "03-26",
            "year": 1971,
            "event": "Историческое событие.",
            "source_title": "Important Event",
            "source_url": "https://example.org/event",
        },
    )

    payload = history_day_orchestrator.run_fact_scenario(
        777200,
        user_message="Что произошло сегодня в истории?",
    )

    assert payload["ok"] is True
    assert "1971" in payload["text"]
    assert "Important Event" in payload["text"]
    assert "Запрос сохранен" in payload["text"]


def test_run_image_scenario_formats_success(monkeypatch):
    monkeypatch.setattr(history_day_orchestrator, "_translate_to_russian", lambda text, telegram_id: text)
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_related_image_user_message",
        lambda telegram_id, *, user_message, date="": {"action": "saved"},
    )
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_related_image_registry",
        lambda: object(),
    )

    def _fake_invoke_tool(*, registry, tool_name, arguments):
        if tool_name == history_day_orchestrator.HISTORY_DAY_IMAGE_TOOL_NAME:
            return {
                "ok": True,
                "date": "03-26",
                "year": 1971,
                "event": "Историческое событие.",
                "image_url": "https://example.org/image.jpg",
                "page_title": "Important Event",
                "source_title": "Important Event",
                "source_url": "https://example.org/event",
            }
        return {
            "ok": True,
            "analysis_text": "На изображении показан важный исторический объект.",
            "analysis_mode": "metadata_fallback",
            "fallback_used": True,
        }

    monkeypatch.setattr(history_day_orchestrator, "_invoke_tool", _fake_invoke_tool)
    payload = history_day_orchestrator.run_image_scenario(
        777201,
        user_message="Покажи изображение по факту дня",
    )

    assert payload["ok"] is True
    assert payload["image_url"] == "https://example.org/image.jpg"
    assert "Анализ" in payload["text"]
    assert "metadata" not in payload["photo_caption"].lower()


def test_run_image_scenario_passes_question_to_analysis(monkeypatch):
    monkeypatch.setattr(history_day_orchestrator, "_translate_to_russian", lambda text, telegram_id: text)
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_related_image_user_message",
        lambda telegram_id, *, user_message, date="": {"action": "saved"},
    )
    monkeypatch.setattr(history_day_orchestrator, "build_related_image_registry", lambda: object())

    captured = {}

    def _fake_invoke_tool(*, registry, tool_name, arguments):
        captured.setdefault("calls", []).append((tool_name, arguments))
        if tool_name == history_day_orchestrator.HISTORY_DAY_IMAGE_TOOL_NAME:
            return {
                "ok": True,
                "date": "03-26",
                "year": 1971,
                "event": "Историческое событие.",
                "image_url": "https://example.org/image.jpg",
                "page_title": "Important Event",
                "page_description": "Historical object",
                "source_title": "Important Event",
                "source_url": "https://example.org/event",
            }
        return {
            "ok": True,
            "analysis_text": "На изображении показан важный объект.",
            "analysis_mode": "vision",
            "fallback_used": False,
        }

    monkeypatch.setattr(history_day_orchestrator, "_invoke_tool", _fake_invoke_tool)
    payload = history_day_orchestrator.run_image_scenario(
        777201,
        user_message="/historyday image Что на нем показано?",
        date="03-26",
        image_question="Что на нем показано?",
    )

    assert payload["ok"] is True
    analysis_call = captured["calls"][1]
    assert analysis_call[0] == history_day_orchestrator.HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME
    assert analysis_call[1]["question"] == "Что на нем показано?"
    assert "Что на нем показано?" in payload["text"]


def test_get_latest_history_day_event_date_returns_recent_fact_or_image(monkeypatch):
    monkeypatch.setattr(
        history_day_orchestrator.memory_svc,
        "list_saved_messages",
        lambda telegram_id, limit=50: [
            {"scenario_tag": "history_day_context", "event_date": ""},
            {"scenario_tag": "history_day_image", "event_date": "03-27"},
            {"scenario_tag": "history_day_fact", "event_date": "03-26"},
        ],
    )

    result = history_day_orchestrator.get_latest_history_day_event_date(777210)
    assert result == "03-27"


def test_get_history_day_memory_snapshot_formats_recent_rows(monkeypatch):
    monkeypatch.setattr(
        history_day_orchestrator.memory_svc,
        "list_saved_messages",
        lambda telegram_id, limit=10: [
            {
                "scenario_tag": "history_day_image",
                "event_date": "03-27",
                "created_at": "2026-03-27 12:00:00",
                "source_kind": "user_message",
                "command_name": "history_day_image",
                "text": "Покажи изображение и объясни его",
            },
            {
                "scenario_tag": "history_day_fact",
                "event_date": "03-27",
                "created_at": "2026-03-27 11:59:00",
                "source_kind": "user_message",
                "command_name": "history_day_fact",
                "text": "Что произошло сегодня в истории?",
            },
        ][:limit],
    )
    monkeypatch.setattr(history_day_orchestrator.memory_svc, "is_memory_search_available", lambda: True)

    snapshot = history_day_orchestrator.get_history_day_memory_snapshot(777211, limit=5)

    assert snapshot["ok"] is True
    assert snapshot["saved_messages_count"] == 2
    assert snapshot["latest_event_date"] == "03-27"
    assert snapshot["items"][0]["scenario_tag"] == "history_day_image"


def test_history_day_smoke_flow_fact_image_context(monkeypatch):
    stored_rows = []

    def _remember_fact(telegram_id, *, user_message, date=""):
        stored_rows.append(
            {
                "scenario_tag": "history_day_fact",
                "event_date": "03-27",
                "created_at": "2026-03-27 11:00:00",
                "text": user_message,
            }
        )
        return {"action": "saved"}

    def _remember_image(telegram_id, *, user_message, date=""):
        stored_rows.append(
            {
                "scenario_tag": "history_day_image",
                "event_date": "03-27",
                "created_at": "2026-03-27 11:01:00",
                "text": user_message,
            }
        )
        return {"action": "saved"}

    monkeypatch.setattr(history_day_orchestrator, "_translate_to_russian", lambda text, telegram_id: "Событие переведено.")
    monkeypatch.setattr(history_day_orchestrator, "remember_fact_of_the_day_user_message", _remember_fact)
    monkeypatch.setattr(history_day_orchestrator, "remember_related_image_user_message", _remember_image)
    monkeypatch.setattr(history_day_orchestrator, "remember_saved_context_user_message", lambda telegram_id, *, user_message: {"action": "saved"})
    monkeypatch.setattr(history_day_orchestrator, "build_fact_of_the_day_registry", lambda: object())
    monkeypatch.setattr(history_day_orchestrator, "build_related_image_registry", lambda: object())
    monkeypatch.setattr(history_day_orchestrator, "build_saved_context_registry", lambda telegram_id: object())
    monkeypatch.setattr(history_day_orchestrator.persona_svc, "build_persona_addon", lambda telegram_id: None)
    monkeypatch.setattr(history_day_orchestrator, "get_user_model", lambda telegram_id: "openrouter")
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_saved_context_messages",
        lambda telegram_id, *, user_message, top_k=3: {
            "messages": [
                {"role": "system", "content": "[Saved Context From LanceDB]\n1. Что произошло сегодня в истории?"},
                {"role": "user", "content": user_message},
            ],
            "retrieval": {
                "found_count": 1,
                "items": [{"source_id": "x1", "text": "Что произошло сегодня в истории?", "event_date": "03-27"}],
                "context_block": "[Saved Context From LanceDB]\n1. Что произошло сегодня в истории?",
            },
        },
    )

    def _fake_invoke_tool(*, registry, tool_name, arguments):
        if tool_name == "history_fact_of_the_day":
            return {
                "ok": True,
                "date": "03-27",
                "year": 2023,
                "event": "Fact event",
                "source_title": "Event Title",
                "source_url": "https://example.org/event",
                "page_title": "Event Title",
                "page_url": "https://example.org/event",
            }
        if tool_name == history_day_orchestrator.HISTORY_DAY_IMAGE_TOOL_NAME:
            return {
                "ok": True,
                "date": "03-27",
                "year": 2023,
                "event": "Fact event",
                "image_url": "https://example.org/image.jpg",
                "page_title": "Event Title",
                "page_description": "Event description",
                "source_title": "Event Title",
                "source_url": "https://example.org/event",
            }
        if tool_name == history_day_orchestrator.HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME:
            return {
                "ok": True,
                "analysis_text": "На изображении показан объект события.",
                "analysis_mode": "vision",
                "fallback_used": False,
            }
        if tool_name == history_day_orchestrator.HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME:
            return {
                "found_count": 1,
                "items": [{"source_id": "x1", "text": "Что произошло сегодня в истории?", "event_date": "03-27"}],
                "context_block": "[Saved Context From LanceDB]\n1. Что произошло сегодня в истории?",
            }
        return {}

    monkeypatch.setattr(history_day_orchestrator, "_invoke_tool", _fake_invoke_tool)

    fact_payload = history_day_orchestrator.run_fact_scenario(777212, user_message="Что произошло сегодня в истории?")
    image_payload = history_day_orchestrator.run_image_scenario(777212, user_message="Покажи изображение по факту дня", date="03-27")
    context_payload = history_day_orchestrator.run_saved_context_scenario(777212, user_message="С каким годом это связано?")

    assert fact_payload["ok"] is True
    assert image_payload["ok"] is True
    assert context_payload["ok"] is True
    assert "2023" in context_payload["text"]
    assert len(stored_rows) == 2


def test_history_day_clear_breaks_followup_context(monkeypatch):
    state = {
        "rows": [
            {
                "scenario_tag": "history_day_fact",
                "event_date": "03-27",
                "created_at": "2026-03-27 11:00:00",
                "text": "Что произошло сегодня в истории?",
            }
        ]
    }

    monkeypatch.setattr(
        history_day_orchestrator.memory_svc,
        "list_saved_messages",
        lambda telegram_id, limit=10: state["rows"][:limit],
    )
    monkeypatch.setattr(history_day_orchestrator.memory_svc, "is_memory_search_available", lambda: True)
    monkeypatch.setattr(
        history_day_orchestrator.memory_svc,
        "clear_user_memory",
        lambda telegram_id, scenario_tag=None: state["rows"].clear() is None or True,
    )
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_saved_context_messages",
        lambda telegram_id, *, user_message, top_k=3: {
            "messages": [
                {"role": "system", "content": "system"},
                {"role": "user", "content": user_message},
            ],
            "retrieval": {
                "found_count": 0,
                "fallback_reason": "no_saved_messages",
            },
        },
    )
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_saved_context_user_message",
        lambda telegram_id, *, user_message: {"action": "saved"},
    )

    clear_payload = history_day_orchestrator.clear_history_day_memory(777213)
    latest_date = history_day_orchestrator.get_latest_history_day_event_date(777213)
    context_payload = history_day_orchestrator.run_saved_context_scenario(
        777213,
        user_message="О чем ты мне только что рассказывал?",
    )

    assert clear_payload["ok"] is True
    assert latest_date == ""
    assert "нет сохраненных" in context_payload["text"].lower()


def test_run_saved_context_scenario_returns_honest_fallback_when_memory_empty(monkeypatch):
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_saved_context_messages",
        lambda telegram_id, *, user_message, top_k=3: {
            "messages": [
                {"role": "system", "content": "system"},
                {"role": "user", "content": user_message},
            ],
            "retrieval": {
                "found_count": 0,
                "fallback_reason": "no_saved_messages",
            },
        },
    )
    saved = {}
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_saved_context_user_message",
        lambda telegram_id, *, user_message: saved.setdefault("value", {"action": "saved"}),
    )

    payload = history_day_orchestrator.run_saved_context_scenario(
        777202,
        user_message="О чем ты мне только что рассказывал?",
    )

    assert payload["ok"] is True
    assert "нет сохраненных" in payload["text"].lower()
    assert saved["value"]["action"] == "saved"


def test_run_saved_context_scenario_uses_llm_with_injected_prompt(monkeypatch):
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_saved_context_messages",
        lambda telegram_id, *, user_message, top_k=3: {
            "messages": [
                {"role": "system", "content": "[Saved Context From LanceDB]\n1. Мы обсуждали мост."},
                {"role": "user", "content": user_message},
            ],
            "retrieval": {
                "found_count": 1,
                "items": [{"source_id": "x1", "text": "Мы обсуждали мост."}],
                "context_block": "[Saved Context From LanceDB]\n1. Мы обсуждали мост.",
            },
        },
    )
    monkeypatch.setattr(history_day_orchestrator, "build_saved_context_registry", lambda telegram_id: object())
    monkeypatch.setattr(
        history_day_orchestrator,
        "_invoke_tool",
        lambda registry, tool_name, arguments: {
            "found_count": 1,
            "items": [{"source_id": "x1", "text": "Мы обсуждали мост."}],
            "context_block": "[Saved Context From LanceDB]\n1. Мы обсуждали мост.",
        },
    )
    monkeypatch.setattr(history_day_orchestrator.persona_svc, "build_persona_addon", lambda telegram_id: None)
    monkeypatch.setattr(history_day_orchestrator, "get_user_model", lambda telegram_id: "openrouter")
    monkeypatch.setattr(
        history_day_orchestrator,
        "get_chat_response",
        lambda **kwargs: ("Ты спрашивал про мост и связанный с ним исторический факт.", 0.0),
    )
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_saved_context_user_message",
        lambda telegram_id, *, user_message: {"action": "saved"},
    )

    payload = history_day_orchestrator.run_saved_context_scenario(
        777203,
        user_message="О чем ты мне только что рассказывал?",
    )

    assert payload["ok"] is True
    assert "мост" in payload["text"].lower()
    assert "сохраненный контекст" in payload["text"].lower()


def test_run_saved_context_scenario_rehydrates_fact_for_year_question(monkeypatch):
    monkeypatch.setattr(history_day_orchestrator, "_translate_to_russian", lambda text, telegram_id: "Сорок человек погибли при пожаре в центре содержания мигрантов в Сьюдад-Хуаресе, Мексика.")
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_saved_context_messages",
        lambda telegram_id, *, user_message, top_k=3: {
            "messages": [
                {"role": "system", "content": "[Saved Context From LanceDB]\n1. Что произошло 27 марта?"},
                {"role": "user", "content": user_message},
            ],
            "retrieval": {
                "found_count": 1,
                "items": [
                    {
                        "source_id": "x1",
                        "text": "Что произошло 27 марта?",
                        "event_date": "03-27",
                        "scenario_tag": "history_day_fact",
                    }
                ],
                "context_block": "[Saved Context From LanceDB]\n1. Что произошло 27 марта?",
            },
        },
    )
    monkeypatch.setattr(history_day_orchestrator, "build_saved_context_registry", lambda telegram_id: object())

    def _fake_invoke_tool(*, registry, tool_name, arguments):
        if tool_name == history_day_orchestrator.HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME:
            return {
                "found_count": 1,
                "items": [
                    {
                        "source_id": "x1",
                        "text": "Что произошло 27 марта?",
                        "event_date": "03-27",
                        "scenario_tag": "history_day_fact",
                    }
                ],
            }
        return {
            "ok": True,
            "date": "03-27",
            "year": 2023,
            "event": "Forty people are killed in a fire at a migrant detention facility in Ciudad Juárez, Mexico.",
            "source_title": "Ciudad Juárez migrant center fire",
            "source_url": "https://en.wikipedia.org/wiki/Ciudad_Ju%C3%A1rez_migrant_center_fire",
        }

    monkeypatch.setattr(history_day_orchestrator, "_invoke_tool", _fake_invoke_tool)
    saved = {}
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_saved_context_user_message",
        lambda telegram_id, *, user_message: saved.setdefault("value", {"action": "saved"}),
    )

    payload = history_day_orchestrator.run_saved_context_scenario(
        777204,
        user_message="С каким годом это связано?",
    )

    assert payload["ok"] is True
    assert "2023" in payload["text"]
    assert "Ciudad Ju" in payload["text"]
    assert saved["value"]["action"] == "saved"


def test_run_fact_scenario_translates_event_to_russian(monkeypatch):
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_fact_of_the_day_user_message",
        lambda telegram_id, *, user_message, date="": {"action": "saved"},
    )
    monkeypatch.setattr(history_day_orchestrator, "build_fact_of_the_day_registry", lambda: object())
    monkeypatch.setattr(
        history_day_orchestrator,
        "_invoke_tool",
        lambda registry, tool_name, arguments: {
            "ok": True,
            "date": "03-27",
            "year": 2023,
            "event": "Forty people are killed in a fire at a migrant detention facility in Ciudad Juárez, Mexico.",
            "source_title": "Ciudad Juárez migrant center fire",
            "source_url": "https://example.org/event",
        },
    )
    monkeypatch.setattr(
        history_day_orchestrator,
        "_translate_to_russian",
        lambda text, telegram_id: "Сорок человек погибли при пожаре в центре содержания мигрантов в Сьюдад-Хуаресе, Мексика.",
    )

    payload = history_day_orchestrator.run_fact_scenario(
        777204,
        user_message="Что произошло сегодня в истории?",
    )

    assert payload["ok"] is True
    assert "Сорок человек" in payload["text"]


def test_run_saved_context_scenario_answers_country_question(monkeypatch):
    monkeypatch.setattr(history_day_orchestrator, "_translate_to_russian", lambda text, telegram_id: "Сорок человек погибли при пожаре в центре содержания мигрантов в Сьюдад-Хуаресе, Мексика.")
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_saved_context_messages",
        lambda telegram_id, *, user_message, top_k=3: {
            "messages": [
                {"role": "system", "content": "[Saved Context From LanceDB]\n1. Что произошло 27 марта?"},
                {"role": "user", "content": user_message},
            ],
            "retrieval": {
                "found_count": 1,
                "items": [{"source_id": "x1", "text": "Что произошло 27 марта?", "event_date": "03-27"}],
                "context_block": "[Saved Context From LanceDB]\n1. Что произошло 27 марта?",
            },
        },
    )
    monkeypatch.setattr(history_day_orchestrator, "build_saved_context_registry", lambda telegram_id: object())

    def _fake_invoke_tool(*, registry, tool_name, arguments):
        if tool_name == history_day_orchestrator.HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME:
            return {"found_count": 1, "items": [{"source_id": "x1", "text": "Что произошло 27 марта?", "event_date": "03-27"}]}
        return {
            "ok": True,
            "date": "03-27",
            "year": 2023,
            "event": "Forty people are killed in a fire at a migrant detention facility in Ciudad Juárez, Mexico.",
            "source_title": "Ciudad Juárez migrant center fire",
            "source_url": "https://en.wikipedia.org/wiki/Ciudad_Ju%C3%A1rez_migrant_center_fire",
        }

    monkeypatch.setattr(history_day_orchestrator, "_invoke_tool", _fake_invoke_tool)
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_saved_context_user_message",
        lambda telegram_id, *, user_message: {"action": "saved"},
    )

    payload = history_day_orchestrator.run_saved_context_scenario(
        777205,
        user_message="В какой стране это было?",
    )

    assert payload["ok"] is True
    assert "Mexico" in payload["text"]


def test_run_saved_context_scenario_answers_location_question(monkeypatch):
    monkeypatch.setattr(history_day_orchestrator, "_translate_to_russian", lambda text, telegram_id: "Сорок человек погибли при пожаре в центре содержания мигрантов в Сьюдад-Хуаресе, Мексика.")
    monkeypatch.setattr(
        history_day_orchestrator,
        "build_saved_context_messages",
        lambda telegram_id, *, user_message, top_k=3: {
            "messages": [
                {"role": "system", "content": "[Saved Context From LanceDB]\n1. Что произошло 27 марта?"},
                {"role": "user", "content": user_message},
            ],
            "retrieval": {
                "found_count": 1,
                "items": [{"source_id": "x1", "text": "Что произошло 27 марта?", "event_date": "03-27"}],
                "context_block": "[Saved Context From LanceDB]\n1. Что произошло 27 марта?",
            },
        },
    )
    monkeypatch.setattr(history_day_orchestrator, "build_saved_context_registry", lambda telegram_id: object())

    def _fake_invoke_tool(*, registry, tool_name, arguments):
        if tool_name == history_day_orchestrator.HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME:
            return {"found_count": 1, "items": [{"source_id": "x1", "text": "Что произошло 27 марта?", "event_date": "03-27"}]}
        return {
            "ok": True,
            "date": "03-27",
            "year": 2023,
            "event": "Forty people are killed in a fire at a migrant detention facility in Ciudad Juárez, Mexico.",
            "source_title": "Ciudad Juárez migrant center fire",
            "source_url": "https://en.wikipedia.org/wiki/Ciudad_Ju%C3%A1rez_migrant_center_fire",
        }

    monkeypatch.setattr(history_day_orchestrator, "_invoke_tool", _fake_invoke_tool)
    monkeypatch.setattr(
        history_day_orchestrator,
        "remember_saved_context_user_message",
        lambda telegram_id, *, user_message: {"action": "saved"},
    )

    payload = history_day_orchestrator.run_saved_context_scenario(
        777206,
        user_message="Где это было?",
    )

    assert payload["ok"] is True
    assert "Ciudad Juárez, Mexico" in payload["text"]
