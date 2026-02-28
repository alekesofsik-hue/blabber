"""
Unit tests for middleware/auth.py — require_role, require_role_callback, with_user_check.
Telebot is mocked; no real Telegram API calls are made.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from middleware.auth import require_role, require_role_callback, with_user_check
from tests.conftest import FakeTelegramUser, FakeMessage


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_user_dict(role_weight: int = 0, is_active: bool = True) -> dict:
    return {
        "telegram_id": 42,
        "role_name": "user" if role_weight == 0 else "admin",
        "role_weight": role_weight,
        "is_active": 1 if is_active else 0,
    }


def _make_bot():
    bot = MagicMock()
    bot.reply_to = MagicMock()
    bot.answer_callback_query = MagicMock()
    return bot


# ── require_role ─────────────────────────────────────────────────────────────

class TestRequireRole:

    def test_allows_admin(self, db):
        bot = _make_bot()
        user_dict = _make_user_dict(role_weight=100)

        with patch("middleware.auth.get_or_create", return_value=user_dict), \
             patch("middleware.auth.is_banned", return_value=False):

            called = []

            @require_role(bot, min_weight=100)
            def handler(message):
                called.append(True)

            msg = FakeMessage(42)
            handler(msg)

        assert called == [True]
        bot.reply_to.assert_not_called()

    def test_blocks_insufficient_role(self, db):
        bot = _make_bot()
        user_dict = _make_user_dict(role_weight=0)

        with patch("middleware.auth.get_or_create", return_value=user_dict), \
             patch("middleware.auth.is_banned", return_value=False):

            called = []

            @require_role(bot, min_weight=100)
            def handler(message):
                called.append(True)

            msg = FakeMessage(42)
            handler(msg)

        assert called == []
        bot.reply_to.assert_called_once()
        args = bot.reply_to.call_args[0]
        assert "прав" in args[1].lower() or "⛔" in args[1]

    def test_blocks_banned_user(self, db):
        bot = _make_bot()
        user_dict = _make_user_dict(role_weight=100)

        with patch("middleware.auth.get_or_create", return_value=user_dict), \
             patch("middleware.auth.is_banned", return_value=True):

            called = []

            @require_role(bot, min_weight=100)
            def handler(message):
                called.append(True)

            msg = FakeMessage(42)
            handler(msg)

        assert called == []
        bot.reply_to.assert_called_once()

    def test_blocks_when_user_creation_fails(self, db):
        bot = _make_bot()

        with patch("middleware.auth.get_or_create", return_value=None):
            called = []

            @require_role(bot, min_weight=0)
            def handler(message):
                called.append(True)

            msg = FakeMessage(42)
            handler(msg)

        assert called == []
        bot.reply_to.assert_called_once()

    def test_moderator_weight_50(self, db):
        bot = _make_bot()
        user_dict = _make_user_dict(role_weight=50)

        with patch("middleware.auth.get_or_create", return_value=user_dict), \
             patch("middleware.auth.is_banned", return_value=False):

            called = []

            @require_role(bot, min_weight=50)
            def handler(message):
                called.append(True)

            msg = FakeMessage(42)
            handler(msg)

        assert called == [True]


# ── require_role_callback ─────────────────────────────────────────────────────

class TestRequireRoleCallback:

    def _make_call(self, user_id: int = 42) -> MagicMock:
        call = MagicMock()
        call.id = "cb123"
        call.from_user = FakeTelegramUser(user_id)
        call.data = "admin_test"
        return call

    def test_allows_admin_callback(self, db):
        bot = _make_bot()
        user_dict = _make_user_dict(role_weight=100)

        with patch("middleware.auth.get_or_create", return_value=user_dict), \
             patch("middleware.auth.is_banned", return_value=False):

            called = []

            @require_role_callback(bot, min_weight=100)
            def cb_handler(call):
                called.append(True)

            cb_handler(self._make_call())

        assert called == [True]

    def test_blocks_low_weight_callback(self, db):
        bot = _make_bot()
        user_dict = _make_user_dict(role_weight=0)

        with patch("middleware.auth.get_or_create", return_value=user_dict), \
             patch("middleware.auth.is_banned", return_value=False):

            called = []

            @require_role_callback(bot, min_weight=100)
            def cb_handler(call):
                called.append(True)

            cb_handler(self._make_call())

        assert called == []
        bot.answer_callback_query.assert_called_once()


# ── with_user_check ───────────────────────────────────────────────────────────

class TestWithUserCheck:

    def test_attaches_user_to_message(self, db):
        bot = _make_bot()
        user_dict = _make_user_dict()

        with patch("middleware.auth.get_or_create", return_value=user_dict), \
             patch("middleware.auth.is_banned", return_value=False):

            received_user = []

            @with_user_check(bot)
            def handler(message):
                received_user.append(message._user)

            msg = FakeMessage(42)
            handler(msg)

        assert received_user[0] is user_dict

    def test_blocks_banned_user(self, db):
        bot = _make_bot()
        user_dict = _make_user_dict()

        with patch("middleware.auth.get_or_create", return_value=user_dict), \
             patch("middleware.auth.is_banned", return_value=True):

            called = []

            @with_user_check(bot)
            def handler(message):
                called.append(True)

            msg = FakeMessage(42)
            handler(msg)

        assert called == []
        bot.reply_to.assert_called_once()

    def test_handles_registration_failure(self, db):
        bot = _make_bot()

        with patch("middleware.auth.get_or_create", return_value=None):
            called = []

            @with_user_check(bot)
            def handler(message):
                called.append(True)

            msg = FakeMessage(42)
            handler(msg)

        assert called == []
        bot.reply_to.assert_called_once()
        args = bot.reply_to.call_args[0]
        assert "ошибка" in args[1].lower() or "⛔" in args[1]
