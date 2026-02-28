"""
Integration tests — full user lifecycle:
  register → use AI → hit limits → admin resets → use AI again.
"""

from __future__ import annotations

import pytest

from services import user_service
from services import limiter
from tests.conftest import FakeTelegramUser


@pytest.fixture()
def tg_user():
    return FakeTelegramUser(777777, "integrator", "Integration")


@pytest.fixture()
def admin_tg_user(monkeypatch):
    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "888888")
    return FakeTelegramUser(888888, "boss", "Boss")


# ── registration ─────────────────────────────────────────────────────────────

def test_first_message_auto_registers(db, tg_user):
    user = user_service.get_or_create(tg_user)
    assert user is not None
    assert user["telegram_id"] == 777777
    assert user["role_name"] == "user"


def test_second_call_returns_same_user(db, tg_user):
    u1 = user_service.get_or_create(tg_user)
    u2 = user_service.get_or_create(tg_user)
    assert u1["id"] == u2["id"]


def test_admin_bootstrap_on_first_message(db, admin_tg_user):
    user = user_service.get_or_create(admin_tg_user)
    assert user["role_name"] == "admin"
    assert user["role_weight"] == 100


def test_admin_bootstrap_upgrades_existing_user(db, tg_user, monkeypatch):
    """If an existing user is later added to ADMIN_TELEGRAM_IDS, they get promoted."""
    user_service.get_or_create(tg_user)  # Create as 'user'
    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "777777")
    import services.user_service as us_mod
    us_mod._INITIAL_ADMIN_IDS = None  # Force reload

    promoted = user_service.get_or_create(tg_user)
    assert promoted["role_name"] == "admin"


# ── ban / unban ───────────────────────────────────────────────────────────────

def test_ban_prevents_access(db, tg_user):
    user_service.get_or_create(tg_user)
    user_service.ban(777777)
    assert user_service.is_banned(777777) is True


def test_unban_restores_access(db, tg_user):
    user_service.get_or_create(tg_user)
    user_service.ban(777777)
    user_service.unban(777777)
    assert user_service.is_banned(777777) is False


def test_unregistered_user_not_banned(db):
    assert user_service.is_banned(9999999) is False


# ── role management ──────────────────────────────────────────────────────────

def test_set_role_to_moderator(db, tg_user):
    user_service.get_or_create(tg_user)
    ok = user_service.set_role(777777, "moderator")
    assert ok is True

    info = user_service.get_user_info(777777)
    assert info["role_name"] == "moderator"


def test_set_role_invalid_name_returns_false(db, tg_user):
    user_service.get_or_create(tg_user)
    ok = user_service.set_role(777777, "superuser")
    assert ok is False


# ── AI usage → limit → reset cycle ───────────────────────────────────────────

def test_usage_increments_counters(db, tg_user):
    user_service.get_or_create(tg_user)
    limiter.increment_usage(777777, 1000)

    remaining = limiter.get_remaining(777777)
    assert remaining["tokens"] == 49000
    assert remaining["requests"] == 99


def test_hit_token_limit(db, tg_user):
    from database import get_connection
    from datetime import datetime, timedelta

    user_service.get_or_create(tg_user)

    future = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tokens_used_today = 50000, limits_reset_at = ? WHERE telegram_id = ?",
            (future, 777777),
        )

    allowed, reason = limiter.check_limits(777777)
    assert allowed is False
    assert reason is not None


def test_admin_reset_re_enables_usage(db, tg_user):
    from database import get_connection
    from datetime import datetime, timedelta
    from repositories.user_repo import reset_limits

    user_service.get_or_create(tg_user)

    future = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tokens_used_today = 50000, limits_reset_at = ? WHERE telegram_id = ?",
            (future, 777777),
        )

    # Admin resets via repo (same call as admin_commands uses)
    reset_limits(777777)

    allowed, reason = limiter.check_limits(777777)
    assert allowed is True
    assert reason is None


# ── full cycle ────────────────────────────────────────────────────────────────

def test_full_lifecycle(db, tg_user):
    """Register → use AI → hit limit → reset → use AI again."""
    # 1. Register
    user = user_service.get_or_create(tg_user)
    assert user is not None

    # 2. Use AI (simulate 10 requests)
    for _ in range(10):
        allowed, _ = limiter.check_limits(777777)
        assert allowed
        limiter.increment_usage(777777, 500)

    rem = limiter.get_remaining(777777)
    assert rem["tokens"] == 45000
    assert rem["requests"] == 90

    # 3. Hit token limit manually
    from database import get_connection
    from datetime import datetime, timedelta

    future = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tokens_used_today = 50000, limits_reset_at = ? WHERE telegram_id = ?",
            (future, 777777),
        )

    allowed, _ = limiter.check_limits(777777)
    assert not allowed

    # 4. Admin resets
    from repositories.user_repo import reset_limits
    reset_limits(777777)

    # 5. Use AI again
    allowed, reason = limiter.check_limits(777777)
    assert allowed
    assert reason is None
