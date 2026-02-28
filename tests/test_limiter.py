"""
Unit tests for services/limiter.py — daily limit checks, reset, edge cases.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from repositories import user_repo
import services.limiter as limiter


@pytest.fixture()
def user(db):
    """Create a standard test user and return their telegram_id."""
    from database import get_connection

    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name='user'").fetchone()["id"]
    user_repo.create(111111, "tester", "Tester", role_id)
    return 111111


# ── check_limits — happy path ────────────────────────────────────────────────

def test_check_limits_allows_new_user(db, user):
    allowed, reason = limiter.check_limits(user)
    assert allowed is True
    assert reason is None


def test_check_limits_unknown_user_is_allowed(db):
    """Unregistered user is allowed (will be registered on first message)."""
    allowed, reason = limiter.check_limits(9999999)
    assert allowed is True


# ── token limit ──────────────────────────────────────────────────────────────

def test_token_limit_exceeded(db, user):
    from database import get_connection

    future = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tokens_used_today = 50001, daily_token_limit = 50000, limits_reset_at = ? WHERE telegram_id = ?",
            (future, user),
        )

    allowed, reason = limiter.check_limits(user)
    assert allowed is False
    assert reason is not None
    assert "Лимит" in reason


# ── request limit ────────────────────────────────────────────────────────────

def test_request_limit_exceeded(db, user):
    from database import get_connection

    future = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET requests_today = 100, daily_request_limit = 100, limits_reset_at = ? WHERE telegram_id = ?",
            (future, user),
        )

    allowed, reason = limiter.check_limits(user)
    assert allowed is False
    assert "запросов" in reason


# ── increment_usage ──────────────────────────────────────────────────────────

def test_increment_usage(db, user):
    limiter.increment_usage(user, tokens_used=500)
    limiter.increment_usage(user, tokens_used=200)

    fetched = user_repo.get_by_telegram_id(user)
    assert fetched["tokens_used_today"] == 700
    assert fetched["requests_today"] == 2


# ── reset_if_needed ──────────────────────────────────────────────────────────

def test_reset_if_needed_fires_when_past(db, user):
    from database import get_connection

    past = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tokens_used_today = 300, requests_today = 10, limits_reset_at = ? WHERE telegram_id = ?",
            (past, user),
        )

    limiter.reset_if_needed(user)

    fetched = user_repo.get_by_telegram_id(user)
    assert fetched["tokens_used_today"] == 0
    assert fetched["requests_today"] == 0


def test_reset_if_needed_skips_when_future(db, user):
    from database import get_connection

    future = (datetime.utcnow() + timedelta(hours=23)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tokens_used_today = 100, requests_today = 5, limits_reset_at = ? WHERE telegram_id = ?",
            (future, user),
        )

    limiter.reset_if_needed(user)

    fetched = user_repo.get_by_telegram_id(user)
    assert fetched["tokens_used_today"] == 100
    assert fetched["requests_today"] == 5


def test_reset_triggers_via_check_limits(db, user):
    """check_limits() internally calls reset_if_needed, so stale counters are cleared."""
    from database import get_connection

    past = (datetime.utcnow() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tokens_used_today = 99999, requests_today = 999, limits_reset_at = ? WHERE telegram_id = ?",
            (past, user),
        )

    allowed, reason = limiter.check_limits(user)
    assert allowed is True  # Counters were reset before the check


# ── get_remaining ────────────────────────────────────────────────────────────

def test_get_remaining_full(db, user):
    rem = limiter.get_remaining(user)
    assert rem["tokens"] == 50000
    assert rem["requests"] == 100


def test_get_remaining_after_usage(db, user):
    limiter.increment_usage(user, 1000)
    rem = limiter.get_remaining(user)
    assert rem["tokens"] == 49000
    assert rem["requests"] == 99


def test_get_remaining_unknown_user(db):
    rem = limiter.get_remaining(9999999)
    assert rem["tokens"] == 50000
    assert rem["requests"] == 100


# ── edge cases ───────────────────────────────────────────────────────────────

def test_check_limits_with_zero_limits(db, user):
    """Zero limits should immediately block the user."""
    from database import get_connection

    future = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET daily_token_limit = 0, tokens_used_today = 0, limits_reset_at = ? WHERE telegram_id = ?",
            (future, user),
        )

    allowed, _ = limiter.check_limits(user)
    assert allowed is False


def test_invalid_reset_at_does_not_crash(db, user):
    """Malformed limits_reset_at should not raise an exception."""
    from database import get_connection

    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET limits_reset_at = 'bad_timestamp' WHERE telegram_id = ?",
            (user,),
        )

    # Should not raise
    limiter.reset_if_needed(user)
