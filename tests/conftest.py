"""
Shared pytest fixtures for blabber tests.

Strategy: each test gets a fresh SQLite file in tmp_path.
database.engine._db_path is patched so all get_connection() calls
hit the temp file, not the production blabber.db.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "database" / "migrations"


def _bootstrap_db(db_file: Path) -> None:
    """Apply all migrations to a fresh SQLite file."""
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()

    for f in sorted(_MIGRATIONS_DIR.iterdir()):
        if f.suffix == ".sql" and f.is_file():
            sql = f.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT OR IGNORE INTO _migrations (filename, checksum) VALUES (?, ?)",
                (f.name, "test"),
            )
            conn.commit()

    conn.close()


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """
    Fresh SQLite DB with all migrations applied. Patches _db_path globally.
    Returns Path to the temp DB file.
    """
    import database.engine as engine_mod

    db_file = tmp_path / "test.db"
    monkeypatch.setattr(engine_mod, "_db_path", db_file)
    _bootstrap_db(db_file)
    yield db_file


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset module-level singletons between tests to prevent cross-test pollution.
    """
    import services.config_registry as cr_mod
    import services.user_service as us_mod

    cr_mod.ConfigRegistry._instance = None
    cr_mod._registry = None
    us_mod._INITIAL_ADMIN_IDS = None

    yield

    cr_mod.ConfigRegistry._instance = None
    cr_mod._registry = None
    us_mod._INITIAL_ADMIN_IDS = None


# ---------------------------------------------------------------------------
# Helpers exposed to test modules
# ---------------------------------------------------------------------------

class FakeTelegramUser:
    """Minimal stub for message.from_user."""

    def __init__(self, user_id: int, username: str | None = None, first_name: str | None = None):
        self.id = user_id
        self.username = username
        self.first_name = first_name or "Test"


class FakeMessage:
    """Minimal stub for telebot.types.Message."""

    def __init__(self, user_id: int, text: str = "hello"):
        self.from_user = FakeTelegramUser(user_id)
        self.text = text
        self.chat = type("Chat", (), {"id": user_id})()
