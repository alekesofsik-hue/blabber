from __future__ import annotations

from datetime import UTC, datetime

from services import history_day_fact_service


def test_normalize_requested_date_supports_today_and_iso():
    now = datetime(2026, 3, 26, 12, 0, tzinfo=UTC)

    today_result = history_day_fact_service.normalize_requested_date("", now=now)
    iso_result = history_day_fact_service.normalize_requested_date("2026-03-26")

    assert today_result["ok"] is True
    assert today_result["date"] == "03-26"
    assert iso_result["ok"] is True
    assert iso_result["date"] == "03-26"


def test_get_fact_of_the_day_normalizes_selected_payload(monkeypatch):
    def _fake_fetch_payload(*, kind: str, month: int, day: int, language: str):
        assert kind == "selected"
        assert month == 3
        assert day == 26
        assert language == "en"
        return {
            "selected": [
                {
                    "year": 1971,
                    "text": "В этот день произошло важное событие.",
                    "pages": [
                        {
                            "titles": {"normalized": "Important Event"},
                            "content_urls": {"desktop": {"page": "https://example.org/event"}},
                            "thumbnail": {"source": "https://example.org/thumb.jpg"},
                        }
                    ],
                }
            ]
        }

    monkeypatch.setattr(history_day_fact_service, "_fetch_payload", _fake_fetch_payload)
    result = history_day_fact_service.get_fact_of_the_day("03-26")

    assert result["ok"] is True
    assert result["date"] == "03-26"
    assert result["year"] == 1971
    assert result["event"] == "В этот день произошло важное событие."
    assert result["source_title"] == "Important Event"
    assert result["source_url"] == "https://example.org/event"
    assert result["origin_kind"] == "selected"
    assert result["fallback_used"] is False


def test_get_fact_of_the_day_falls_back_to_events(monkeypatch):
    def _fake_fetch_payload(*, kind: str, month: int, day: int, language: str):
        if kind == "selected":
            return {
                "selected": [
                    {
                        "year": 1700,
                        "text": "Факт без изображения.",
                        "pages": [],
                    }
                ]
            }
        return {
            "events": [
                {
                    "year": 1885,
                    "text": "Резервный исторический факт.",
                    "pages": [
                        {
                            "titles": {"normalized": "Fallback Event"},
                            "content_urls": {"desktop": {"page": "https://example.org/fallback"}},
                            "thumbnail": {"source": "https://example.org/fallback-thumb.jpg"},
                        }
                    ],
                }
            ]
        }

    monkeypatch.setattr(history_day_fact_service, "_fetch_payload", _fake_fetch_payload)
    result = history_day_fact_service.get_fact_of_the_day("03/26")

    assert result["ok"] is True
    assert result["origin_kind"] == "events"
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == "selected_unavailable_empty_or_without_image"
    assert result["event"] == "Резервный исторический факт."


def test_get_fact_of_the_day_returns_structured_error_for_invalid_date():
    result = history_day_fact_service.get_fact_of_the_day("99-99")

    assert result["ok"] is False
    assert result["error"] == "invalid_date"


def test_get_fact_of_the_day_returns_structured_error_when_upstream_unavailable(monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("upstream down")

    monkeypatch.setattr(history_day_fact_service, "_fetch_payload", _boom)
    result = history_day_fact_service.get_fact_of_the_day("03-26")

    assert result["ok"] is False
    assert result["error"] == "history_fact_with_image_unavailable"
    assert result["fallback_used"] is True


def test_get_fact_of_the_day_returns_error_when_no_fact_has_image(monkeypatch):
    def _fake_fetch_payload(*, kind: str, month: int, day: int, language: str):
        if kind == "selected":
            return {
                "selected": [
                    {
                        "year": 1700,
                        "text": "Факт без изображения.",
                        "pages": [],
                    }
                ]
            }
        return {
            "events": [
                {
                    "year": 1885,
                    "text": "Тоже без изображения.",
                    "pages": [],
                }
            ]
        }

    monkeypatch.setattr(history_day_fact_service, "_fetch_payload", _fake_fetch_payload)
    result = history_day_fact_service.get_fact_of_the_day("03-26")

    assert result["ok"] is False
    assert result["error"] == "history_fact_with_image_unavailable"
    assert result["fallback_reason"] == "wikimedia_unavailable_or_no_image"
