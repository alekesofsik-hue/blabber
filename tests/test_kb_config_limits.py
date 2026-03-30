from __future__ import annotations

from repositories import user_repo
from repositories.config_repo import get as config_get
from database import get_connection
from services import knowledge_service


def _create_user(db, telegram_id: int = 991001) -> int:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user_repo.create(telegram_id, "kb_limit_tester", "KB Limit", role_id)
    return telegram_id


def test_kb_max_doc_size_default_seed_is_3_mib(db):
    row = config_get("kb_max_doc_size_kb")
    assert row is not None
    assert row["value"] == "3072"
    assert knowledge_service.get_max_doc_size_bytes() == 3072 * 1024
    assert knowledge_service.format_doc_size_limit() == "3 МБ"


def test_index_document_uses_configurable_doc_size_limit(db):
    telegram_id = _create_user(db, 991002)

    from services.config_registry import get_config_registry

    registry = get_config_registry()
    registry.load(None)
    registry.set("kb_max_doc_size_kb", 1, "int", "kb")

    ok, msg = knowledge_service.index_document(
        telegram_id,
        "big.txt",
        b"ab" * 1024,
    )
    assert ok is False
    assert "макс. 1 КБ" in msg
