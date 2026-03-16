from __future__ import annotations

from services import profile_service, user_service
from tests.conftest import FakeTelegramUser


def test_profile_add_preference_sets_kind(db):
    user_service.get_or_create(FakeTelegramUser(200, "prefuser", "Pref"))
    ok, _ = profile_service.add_preference(200, "Отвечай кратко")
    assert ok is True

    items = profile_service.get_items_with_ids(200)
    assert len(items) == 1
    assert items[0]["kind"] == "preference"
    assert items[0]["fact"] == "Отвечай кратко"

