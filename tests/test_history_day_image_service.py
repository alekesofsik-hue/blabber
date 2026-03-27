from __future__ import annotations

from services import history_day_image_service


def test_get_related_image_for_fact_returns_normalized_image_payload(monkeypatch):
    monkeypatch.setattr(
        history_day_image_service.fact_svc,
        "get_fact_of_the_day",
        lambda date="", language="en": {
            "ok": True,
            "date": "03-26",
            "language": language,
            "year": 1971,
            "event": "Историческое событие.",
            "page_title": "Important Event",
            "page_url": "https://example.org/page",
            "page_description": "Historical object",
            "image_url": "https://example.org/image.jpg",
            "thumbnail_url": "https://example.org/thumb.jpg",
            "source_url": "https://example.org/page",
            "source_title": "Important Event",
            "fallback_used": False,
            "fallback_reason": None,
        },
    )

    result = history_day_image_service.get_related_image_for_fact("03-26")

    assert result["ok"] is True
    assert result["image_url"] == "https://example.org/image.jpg"
    assert result["page_title"] == "Important Event"
    assert result["image_origin"] == "wikimedia_page_image"


def test_get_related_image_for_fact_returns_error_when_image_missing(monkeypatch):
    monkeypatch.setattr(
        history_day_image_service.fact_svc,
        "get_fact_of_the_day",
        lambda date="", language="en": {
            "ok": True,
            "date": "03-26",
            "language": language,
            "year": 1971,
            "event": "Историческое событие.",
            "page_title": "Important Event",
            "page_url": "https://example.org/page",
            "page_description": "Historical object",
            "image_url": "",
            "thumbnail_url": "",
            "fallback_used": False,
            "fallback_reason": None,
        },
    )
    result = history_day_image_service.get_related_image_for_fact("03-26")

    assert result["ok"] is False
    assert result["error"] == "image_not_found"
    assert result["fallback_used"] is True


def test_analyze_related_image_uses_metadata_fallback_when_vision_unavailable(monkeypatch):
    monkeypatch.setattr(history_day_image_service, "_get_vision_client", lambda: (None, None))

    result = history_day_image_service.analyze_related_image(
        image_url="https://example.org/image.jpg",
        event="Историческое событие.",
        year=1971,
        page_title="Important Event",
        page_description="Historical object",
    )

    assert result["ok"] is True
    assert result["analysis_mode"] == "metadata_fallback"
    assert result["fallback_used"] is True
    assert "Important Event" in result["analysis_text"]


def test_analyze_related_image_uses_vision_when_available(monkeypatch):
    class _FakeResponse:
        def __init__(self):
            self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": "Это мост и его обрушение связано с событием."})()})()]

    class _FakeCompletions:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeChat:
        def __init__(self):
            self.completions = _FakeCompletions()

    class _FakeClient:
        def __init__(self):
            self.chat = _FakeChat()

    monkeypatch.setattr(history_day_image_service, "_get_vision_client", lambda: (_FakeClient(), "gpt-4o-mini"))

    result = history_day_image_service.analyze_related_image(
        image_url="https://example.org/image.jpg",
        event="Историческое событие.",
        year=1971,
        page_title="Important Event",
        page_description="Historical object",
    )

    assert result["ok"] is True
    assert result["analysis_mode"] == "vision"
    assert result["fallback_used"] is False
    assert "мост" in result["analysis_text"].lower()


def test_analyze_related_image_passes_question_to_vision_prompt(monkeypatch):
    captured = {}

    class _FakeResponse:
        def __init__(self):
            self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": "На изображении показан флаг."})()})()]

    class _FakeCompletions:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return _FakeResponse()

    class _FakeChat:
        def __init__(self):
            self.completions = _FakeCompletions()

    class _FakeClient:
        def __init__(self):
            self.chat = _FakeChat()

    monkeypatch.setattr(history_day_image_service, "_get_vision_client", lambda: (_FakeClient(), "gpt-4o-mini"))

    result = history_day_image_service.analyze_related_image(
        image_url="https://example.org/image.jpg",
        event="Историческое событие.",
        year=1971,
        page_title="Important Event",
        page_description="Historical object",
        question="Какого цвета объект на изображении?",
    )

    assert result["ok"] is True
    user_payload = captured["kwargs"]["messages"][1]["content"][0]["text"]
    assert "Какого цвета объект на изображении?" in user_payload
