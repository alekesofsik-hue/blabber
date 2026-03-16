from __future__ import annotations

import json

from repositories import auto_memory_repo
from services import user_service
from tests.conftest import FakeTelegramUser


def test_auto_memory_settings_default_enabled(db):
    user_service.get_or_create(FakeTelegramUser(123, "u", "U"))
    settings = auto_memory_repo.get_user_settings(123)
    assert settings is not None
    assert settings["enabled"] is True


def test_auto_memory_toggle(db):
    user_service.get_or_create(FakeTelegramUser(124, "u2", "U2"))
    assert auto_memory_repo.set_enabled(124, False) is True
    settings = auto_memory_repo.get_user_settings(124)
    assert settings is not None
    assert settings["enabled"] is False


def test_memory_suggestion_crud(db):
    user_service.get_or_create(FakeTelegramUser(125, "u3", "U3"))
    settings = auto_memory_repo.get_user_settings(125)
    uid = settings["user_db_id"]

    items = [{"kind": "fact", "text": "Меня зовут Алексей", "evidence": "Меня зовут Алексей", "status": "pending"}]
    auto_memory_repo.create_suggestion("sug1", uid, json.dumps(items, ensure_ascii=False))

    row = auto_memory_repo.get_suggestion("sug1", uid)
    assert row is not None
    assert row["status"] == "pending"

    items[0]["status"] = "saved"
    auto_memory_repo.update_items_json("sug1", uid, json.dumps(items, ensure_ascii=False))
    row2 = auto_memory_repo.get_suggestion("sug1", uid)
    assert json.loads(row2["items_json"])[0]["status"] == "saved"

    auto_memory_repo.set_status("sug1", uid, "dismissed")
    row3 = auto_memory_repo.get_suggestion("sug1", uid)
    assert row3["status"] == "dismissed"

