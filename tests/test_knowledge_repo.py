from __future__ import annotations

import sqlite3
from pathlib import Path

from database import get_connection
from repositories import knowledge_repo, user_repo
from services import knowledge_service


def _create_user(db, telegram_id: int = 777001) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "kb_tester", "KB", role_id)
    return telegram_id, user["id"]


def test_add_chunks_generates_chunk_uids_and_lookup(db):
    telegram_id, user_db_id = _create_user(db)
    doc_id = knowledge_repo.add_document(user_db_id, "notes.txt", 123, 2)

    chunk_uids = knowledge_repo.add_chunks(
        doc_id,
        user_db_id,
        ["alpha text", "beta text"],
        [None, None],
    )

    assert len(chunk_uids) == 2
    assert len(set(chunk_uids)) == 2
    assert all(len(uid) == 32 for uid in chunk_uids)

    rows = knowledge_repo.get_all_chunks(user_db_id)
    assert len(rows) == 2
    assert {row["chunk_uid"] for row in rows} == set(chunk_uids)

    by_doc = knowledge_repo.get_chunks_by_doc(doc_id, user_db_id)
    assert [row["chunk_idx"] for row in by_doc] == [0, 1]

    subset = knowledge_repo.get_chunks_by_uids(user_db_id, [chunk_uids[1]])
    assert len(subset) == 1
    assert subset[0]["content"] == "beta text"

    lookup = knowledge_service.get_chunk_lookup(telegram_id, [chunk_uids[0]])
    assert lookup[chunk_uids[0]]["content"] == "alpha text"
    assert lookup[chunk_uids[0]]["doc_name"] == "notes.txt"
    assert lookup[chunk_uids[0]]["chunk_idx"] == 0


def test_chunk_uid_migration_backfills_existing_rows(tmp_path):
    db_file = tmp_path / "migration.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    migrations_dir = Path(__file__).resolve().parent.parent / "database" / "migrations"
    for name in ("001_initial.sql", "006_knowledge_base.sql", "007_kb_embedding.sql"):
        conn.executescript((migrations_dir / name).read_text(encoding="utf-8"))

    user_role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    conn.execute(
        """
        INSERT INTO users (telegram_id, username, first_name, role_id, limits_reset_at)
        VALUES (?, ?, ?, ?, datetime('now', '+24 hours'))
        """,
        (999001, "legacy_user", "Legacy", user_role_id),
    )
    user_id = conn.execute("SELECT id FROM users WHERE telegram_id = 999001").fetchone()["id"]
    conn.execute(
        "INSERT INTO kb_documents (user_id, name, size_bytes, chunk_count) VALUES (?, ?, ?, ?)",
        (user_id, "legacy.txt", 42, 1),
    )
    doc_id = conn.execute("SELECT id FROM kb_documents WHERE user_id = ?", (user_id,)).fetchone()["id"]
    conn.execute(
        "INSERT INTO kb_chunks (doc_id, user_id, content, chunk_idx, embedding) VALUES (?, ?, ?, ?, ?)",
        (doc_id, user_id, "legacy chunk", 0, None),
    )
    conn.commit()

    conn.executescript((migrations_dir / "012_kb_chunk_uid.sql").read_text(encoding="utf-8"))
    row = conn.execute("SELECT chunk_uid FROM kb_chunks").fetchone()
    assert row["chunk_uid"] is not None
    assert len(row["chunk_uid"]) == 32
    conn.close()
