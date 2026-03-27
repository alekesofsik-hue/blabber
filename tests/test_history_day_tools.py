from __future__ import annotations

from services import history_day_tools
from services.history_day_haystack_adapter import CompatibleToolCall
from services.history_day_real_haystack import invoke_tool_call_via_haystack


def test_build_fact_of_the_day_registry_exposes_tool_schema():
    registry = history_day_tools.build_fact_of_the_day_registry()
    schemas = registry.openai_schemas()

    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == history_day_tools.HISTORY_DAY_FACT_TOOL_NAME
    assert "сегодня в истории" in schemas[0]["function"]["description"].lower()


def test_build_fact_of_the_day_messages_includes_prompt_instruction():
    messages = history_day_tools.build_fact_of_the_day_messages(
        user_message="Что произошло сегодня в истории?",
        context_blocks=["[Память]\nПользователь любит историю науки"],
    )

    assert len(messages) == 2
    assert history_day_tools.HISTORY_DAY_FACT_TOOL_NAME in messages[0]["content"]
    assert "[Память]" in messages[0]["content"]
    assert messages[1]["content"] == "Что произошло сегодня в истории?"


def test_build_related_image_registry_exposes_image_tools():
    registry = history_day_tools.build_related_image_registry()
    schemas = registry.openai_schemas()
    names = [schema["function"]["name"] for schema in schemas]

    assert history_day_tools.HISTORY_DAY_FACT_TOOL_NAME in names
    assert history_day_tools.HISTORY_DAY_IMAGE_TOOL_NAME in names
    assert history_day_tools.HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME in names


def test_build_related_image_messages_includes_two_step_prompt():
    messages = history_day_tools.build_related_image_messages(
        user_message="Покажи изображение по факту дня и объясни его",
        context_blocks=["[Память]\nПользователь любит исторические иллюстрации"],
    )

    assert len(messages) == 2
    assert history_day_tools.HISTORY_DAY_IMAGE_TOOL_NAME in messages[0]["content"]
    assert history_day_tools.HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME in messages[0]["content"]
    assert "[Память]" in messages[0]["content"]


def test_build_saved_context_registry_exposes_lookup_tool():
    registry = history_day_tools.build_saved_context_registry(telegram_id=777003)
    schemas = registry.openai_schemas()

    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == history_day_tools.HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME
    assert "lancedb-памяти" in schemas[0]["function"]["description"].lower()


def test_build_saved_context_messages_injects_retrieved_context(monkeypatch):
    monkeypatch.setattr(
        history_day_tools.context_svc,
        "retrieve_saved_context",
        lambda telegram_id, *, query, top_k=3: {
            "ok": True,
            "query": query,
            "items": [{"source_id": "x1", "text": "Мы обсуждали событие 26 марта."}],
            "context_block": "[Saved Context From LanceDB]\n1. Мы обсуждали событие 26 марта.",
            "found_count": 1,
            "fallback_used": False,
            "fallback_reason": None,
        },
    )

    payload = history_day_tools.build_saved_context_messages(
        777003,
        user_message="О чем ты мне только что рассказывал?",
    )

    assert len(payload["messages"]) == 2
    assert history_day_tools.HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME in payload["messages"][0]["content"]
    assert "[Saved Context From LanceDB]" in payload["messages"][0]["content"]
    assert payload["retrieval"]["found_count"] == 1


def test_remember_fact_of_the_day_user_message_delegates_to_memory_service(monkeypatch):
    captured = {}

    def _fake_save_user_message(telegram_id: int, **kwargs):
        captured["telegram_id"] = telegram_id
        captured["kwargs"] = kwargs
        return {"ok": True, "action": "saved"}

    monkeypatch.setattr(history_day_tools.memory_svc, "save_user_message", _fake_save_user_message)
    result = history_day_tools.remember_fact_of_the_day_user_message(
        777001,
        user_message="Что произошло 26 марта?",
        date="03-26",
    )

    assert result["action"] == "saved"
    assert captured["telegram_id"] == 777001
    assert captured["kwargs"]["scenario_tag"] == history_day_tools.HISTORY_DAY_FACT_SCENARIO_TAG
    assert captured["kwargs"]["event_date"] == "03-26"
    assert captured["kwargs"]["text"] == "Что произошло 26 марта?"


def test_remember_related_image_user_message_delegates_to_memory_service(monkeypatch):
    captured = {}

    def _fake_save_user_message(telegram_id: int, **kwargs):
        captured["telegram_id"] = telegram_id
        captured["kwargs"] = kwargs
        return {"ok": True, "action": "saved"}

    monkeypatch.setattr(history_day_tools.memory_svc, "save_user_message", _fake_save_user_message)
    result = history_day_tools.remember_related_image_user_message(
        777002,
        user_message="Покажи изображение по факту 26 марта",
        date="03-26",
    )

    assert result["action"] == "saved"
    assert captured["telegram_id"] == 777002
    assert captured["kwargs"]["scenario_tag"] == history_day_tools.HISTORY_DAY_IMAGE_SCENARIO_TAG
    assert captured["kwargs"]["event_date"] == "03-26"
    assert captured["kwargs"]["text"] == "Покажи изображение по факту 26 марта"


def test_remember_saved_context_user_message_delegates_to_memory_service(monkeypatch):
    captured = {}

    def _fake_save_user_message(telegram_id: int, **kwargs):
        captured["telegram_id"] = telegram_id
        captured["kwargs"] = kwargs
        return {"ok": True, "action": "saved"}

    monkeypatch.setattr(history_day_tools.memory_svc, "save_user_message", _fake_save_user_message)
    result = history_day_tools.remember_saved_context_user_message(
        777004,
        user_message="С каким годом это связано?",
    )

    assert result["action"] == "saved"
    assert captured["telegram_id"] == 777004
    assert captured["kwargs"]["scenario_tag"] == history_day_tools.HISTORY_DAY_CONTEXT_SCENARIO_TAG
    assert captured["kwargs"]["source_kind"] == "user_clarification"
    assert captured["kwargs"]["text"] == "С каким годом это связано?"


def test_fact_of_the_day_tool_runs_via_real_haystack(monkeypatch):
    monkeypatch.setattr(
        history_day_tools.fact_svc,
        "get_fact_of_the_day",
        lambda date="", language="en": {
            "ok": True,
            "date": date or "03-26",
            "year": 1971,
            "event": "Тестовый исторический факт.",
            "language": language,
        },
    )
    registry = history_day_tools.build_fact_of_the_day_registry()

    observation = invoke_tool_call_via_haystack(
        tool_call=CompatibleToolCall(
            id="fact_call_1",
            name=history_day_tools.HISTORY_DAY_FACT_TOOL_NAME,
            arguments='{"date":"03-26","language":"en"}',
        ),
        registry=registry,
    )

    assert observation["error"] is False
    assert observation["result"]["year"] == 1971
    assert observation["result"]["event"] == "Тестовый исторический факт."


def test_related_image_tool_runs_via_real_haystack(monkeypatch):
    monkeypatch.setattr(
        history_day_tools.image_svc,
        "get_related_image_for_fact",
        lambda date="", language="en": {
            "ok": True,
            "date": date or "03-26",
            "year": 1971,
            "event": "Тестовый факт.",
            "image_url": "https://example.org/image.jpg",
            "page_title": "Important Event",
        },
    )
    registry = history_day_tools.build_related_image_registry()

    observation = invoke_tool_call_via_haystack(
        tool_call=CompatibleToolCall(
            id="img_call_1",
            name=history_day_tools.HISTORY_DAY_IMAGE_TOOL_NAME,
            arguments='{"date":"03-26","language":"en"}',
        ),
        registry=registry,
    )

    assert observation["error"] is False
    assert observation["result"]["image_url"] == "https://example.org/image.jpg"
    assert observation["result"]["page_title"] == "Important Event"


def test_image_analysis_tool_runs_via_real_haystack(monkeypatch):
    monkeypatch.setattr(
        history_day_tools.image_svc,
        "analyze_related_image",
        lambda image_url, event="", year=None, page_title="", page_description="": {
            "ok": True,
            "analysis_text": "На изображении показан важный исторический объект.",
            "analysis_mode": "metadata_fallback",
            "image_url": image_url,
        },
    )
    registry = history_day_tools.build_related_image_registry()

    observation = invoke_tool_call_via_haystack(
        tool_call=CompatibleToolCall(
            id="img_call_2",
            name=history_day_tools.HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME,
            arguments='{"image_url":"https://example.org/image.jpg","event":"Факт","year":1971}',
        ),
        registry=registry,
    )

    assert observation["error"] is False
    assert observation["result"]["analysis_mode"] == "metadata_fallback"
    assert "исторический объект" in observation["result"]["analysis_text"].lower()


def test_saved_context_tool_runs_via_real_haystack(monkeypatch):
    monkeypatch.setattr(
        history_day_tools.context_svc,
        "retrieve_saved_context",
        lambda telegram_id, *, query, top_k=3: {
            "ok": True,
            "query": query,
            "items": [{"source_id": "x1", "text": "Мы обсуждали мост и 1971 год."}],
            "context_block": "[Saved Context From LanceDB]\n1. Мы обсуждали мост и 1971 год.",
            "found_count": 1,
            "fallback_used": False,
            "fallback_reason": None,
        },
    )
    registry = history_day_tools.build_saved_context_registry(telegram_id=777005)

    observation = invoke_tool_call_via_haystack(
        tool_call=CompatibleToolCall(
            id="ctx_call_1",
            name=history_day_tools.HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME,
            arguments='{"query":"О чем ты мне только что рассказывал?","top_k":3}',
        ),
        registry=registry,
    )

    assert observation["error"] is False
    assert observation["result"]["found_count"] == 1
    assert "[Saved Context From LanceDB]" in observation["result"]["context_block"]
