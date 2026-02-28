"""
Unit tests for repositories/user_repo.py using in-memory SQLite.
"""

from __future__ import annotations

import pytest
from repositories import user_repo


@pytest.fixture()
def role_ids(db):
    """Return {'user': id, 'moderator': id, 'admin': id} from seeded roles."""
    from database import get_connection

    with get_connection() as conn:
        rows = conn.execute("SELECT id, name FROM roles").fetchall()
    return {r["name"]: r["id"] for r in rows}


# ── create & get ────────────────────────────────────────────────────────────

def test_create_and_get(db, role_ids):
    user = user_repo.create(123456, "alice", "Alice", role_ids["user"])
    assert user is not None
    assert user["telegram_id"] == 123456
    assert user["username"] == "alice"
    assert user["role_name"] == "user"
    assert user["role_weight"] == 0

    fetched = user_repo.get_by_telegram_id(123456)
    assert fetched is not None
    assert fetched["id"] == user["id"]


def test_get_nonexistent_returns_none(db):
    assert user_repo.get_by_telegram_id(999) is None


def test_create_without_username(db, role_ids):
    user = user_repo.create(111, None, "Bob", role_ids["user"])
    assert user["username"] is None
    assert user["first_name"] == "Bob"


def test_create_with_preferred_model(db, role_ids):
    user = user_repo.create(222, "carol", "Carol", role_ids["user"], preferred_model="gigachat")
    assert user["preferred_model"] == "gigachat"


# ── update_role ─────────────────────────────────────────────────────────────

def test_update_role(db, role_ids):
    user_repo.create(300, "dave", "Dave", role_ids["user"])
    updated = user_repo.update_role(300, role_ids["admin"])
    assert updated is True

    fetched = user_repo.get_by_telegram_id(300)
    assert fetched["role_name"] == "admin"
    assert fetched["role_weight"] == 100


def test_update_role_nonexistent_returns_false(db, role_ids):
    result = user_repo.update_role(9999, role_ids["admin"])
    assert result is False


# ── ban / unban ─────────────────────────────────────────────────────────────

def test_ban_and_unban(db, role_ids):
    user_repo.create(400, "eve", "Eve", role_ids["user"])

    assert user_repo.set_active(400, False) is True
    fetched = user_repo.get_by_telegram_id(400)
    assert fetched["is_active"] == 0

    assert user_repo.set_active(400, True) is True
    fetched = user_repo.get_by_telegram_id(400)
    assert fetched["is_active"] == 1


# ── limits ──────────────────────────────────────────────────────────────────

def test_update_limits(db, role_ids):
    user_repo.create(500, "frank", "Frank", role_ids["user"])
    result = user_repo.update_limits(500, daily_token_limit=1000, daily_request_limit=5)
    assert result is True

    fetched = user_repo.get_by_telegram_id(500)
    assert fetched["daily_token_limit"] == 1000
    assert fetched["daily_request_limit"] == 5


def test_reset_limits(db, role_ids):
    user_repo.create(600, "grace", "Grace", role_ids["user"])

    from database import get_connection
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tokens_used_today = 100, requests_today = 5 WHERE telegram_id = ?",
            (600,),
        )

    user_repo.reset_limits(600)
    fetched = user_repo.get_by_telegram_id(600)
    assert fetched["tokens_used_today"] == 0
    assert fetched["requests_today"] == 0


# ── list & count ─────────────────────────────────────────────────────────────

def test_list_users(db, role_ids):
    for i, name in enumerate(("u1", "u2", "u3"), start=700):
        user_repo.create(i, name, name, role_ids["user"])

    users = user_repo.list_users(offset=0, limit=10)
    assert len(users) == 3


def test_list_users_role_filter(db, role_ids):
    user_repo.create(800, "mod1", "Mod", role_ids["moderator"])
    user_repo.create(801, "user1", "Usr", role_ids["user"])

    mods = user_repo.list_users(role_filter="moderator")
    assert len(mods) == 1
    assert mods[0]["telegram_id"] == 800


def test_count_users(db, role_ids):
    for i in range(810, 815):
        user_repo.create(i, None, "X", role_ids["user"])
    assert user_repo.count_users() == 5


# ── search ──────────────────────────────────────────────────────────────────

def test_search_by_telegram_id(db, role_ids):
    user_repo.create(900, "searchme", "Search", role_ids["user"])
    results = user_repo.search_users("900")
    assert len(results) == 1
    assert results[0]["telegram_id"] == 900


def test_search_by_username(db, role_ids):
    user_repo.create(901, "findme", "Find", role_ids["user"])
    results = user_repo.search_users("findme")
    assert len(results) == 1
    assert results[0]["username"] == "findme"


def test_search_empty_query(db):
    results = user_repo.search_users("")
    assert results == []
