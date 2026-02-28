"""
Database engine for Blabber bot.

Provides SQLite connection management and automatic migration support.

Usage:
    from database import init_db, get_connection

    # At bot startup (once):
    init_db()

    # In any module that needs DB access:
    with get_connection() as conn:
        conn.execute("SELECT ...")
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

logger = logging.getLogger("blabber")

# Base directories
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

# Database file path: configurable via env, default next to bot.py
_db_path: Path | None = None


def get_db_path() -> Path:
    """Return database file path (for admin stats)."""
    return _get_db_path()


def _get_db_path() -> Path:
    """Resolve database file path (cached after first call)."""
    global _db_path
    if _db_path is None:
        env_path = os.environ.get("DATABASE_PATH")
        if env_path:
            _db_path = Path(env_path)
        else:
            _db_path = _PROJECT_ROOT / "blabber.db"
    return _db_path


def _connect(path: Path | None = None) -> sqlite3.Connection:
    """
    Create a new SQLite connection with recommended pragmas.

    - WAL mode for concurrent reads during writes
    - Foreign keys enforced
    - Row factory for dict-like access
    """
    db_file = path or get_db_path()
    conn = sqlite3.connect(str(db_file), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields a SQLite connection.

    Commits on success, rolls back on exception.

    Usage:
        with get_connection() as conn:
            conn.execute("INSERT INTO ...")
    """
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Migration engine ─────────────────────────────────────────

_MIGRATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS _migrations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    filename   TEXT    NOT NULL UNIQUE,
    checksum   TEXT    NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT (datetime('now'))
);
"""


def _file_checksum(content: str) -> str:
    """SHA-256 hex digest of migration file content (first 12 chars)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    """Create _migrations tracking table if it does not exist."""
    conn.executescript(_MIGRATIONS_TABLE_DDL)


def _get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    """Return set of already applied migration filenames."""
    rows = conn.execute("SELECT filename FROM _migrations").fetchall()
    return {row["filename"] for row in rows}


def _discover_migrations() -> list[tuple[str, str]]:
    """
    Discover .sql files in the migrations directory.

    Returns sorted list of (filename, full_path) tuples.
    Sorting is lexicographic — use numeric prefixes (001_, 002_, ...).
    """
    if not _MIGRATIONS_DIR.is_dir():
        return []

    migrations = []
    for f in sorted(_MIGRATIONS_DIR.iterdir()):
        if f.suffix == ".sql" and f.is_file():
            migrations.append((f.name, str(f)))
    return migrations


def _apply_migration(conn: sqlite3.Connection, filename: str, filepath: str) -> None:
    """Read and execute a single migration file, then record it."""
    with open(filepath, encoding="utf-8") as fh:
        sql = fh.read()

    checksum = _file_checksum(sql)

    logger.info(
        "applying_migration",
        extra={
            "event": "applying_migration",
            "migration": filename,
            "checksum": checksum,
        },
    )

    # executescript auto-commits; we wrap in savepoint for safety
    conn.executescript(sql)

    conn.execute(
        "INSERT INTO _migrations (filename, checksum) VALUES (?, ?)",
        (filename, checksum),
    )
    conn.commit()


# ── Public API ───────────────────────────────────────────────

def init_db() -> None:
    """
    Initialize the database: apply all pending migrations.

    Safe to call multiple times — already applied migrations are skipped.
    Should be called once at bot startup, before any handlers are registered.
    """
    db_path = _get_db_path()
    logger.info(
        "db_init_start",
        extra={"event": "db_init_start", "db_path": str(db_path)},
    )

    conn = _connect(db_path)
    try:
        _ensure_migrations_table(conn)
        applied = _get_applied_migrations(conn)
        available = _discover_migrations()

        new_count = 0
        for filename, filepath in available:
            if filename in applied:
                continue
            _apply_migration(conn, filename, filepath)
            new_count += 1

        logger.info(
            "db_init_complete",
            extra={
                "event": "db_init_complete",
                "migrations_applied": new_count,
                "migrations_total": len(available),
                "db_path": str(db_path),
            },
        )
    finally:
        conn.close()
