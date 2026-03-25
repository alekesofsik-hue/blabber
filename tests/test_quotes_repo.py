from __future__ import annotations

from database import get_connection
from repositories import quotes_repo, user_repo


def _create_user(db, telegram_id: int = 555001) -> int:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user_repo.create(telegram_id, "quotes_tester", "Quotes", role_id)
    return telegram_id


def _vector(axis: int = 0, dim: int = quotes_repo.EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_add_and_search_quote_vector(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id = _create_user(db)

    lance_id = quotes_repo.add_quote(
        telegram_id,
        "Балабол снова сказал что-то странно мудрое",
        _vector(0),
    )

    row = quotes_repo.get_quote_by_lance_id(telegram_id, lance_id)
    assert row is not None
    assert row["text"] == "Балабол снова сказал что-то странно мудрое"

    results = quotes_repo.semantic_search(telegram_id, _vector(0), top_k=3)
    assert len(results) == 1
    assert results[0]["lance_id"] == lance_id


def test_delete_quote_removes_sqlite_row(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id = _create_user(db, telegram_id=555002)

    lance_id = quotes_repo.add_quote(telegram_id, "Удаляемая цитата", _vector(1))
    row = quotes_repo.get_quote_by_lance_id(telegram_id, lance_id)
    assert row is not None

    assert quotes_repo.delete_quote(telegram_id, row["id"]) is True
    assert quotes_repo.get_quote_by_lance_id(telegram_id, lance_id) is None
    assert quotes_repo.semantic_search(telegram_id, _vector(1), top_k=3) == []


def test_delete_all_quotes_drops_vector_table(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id = _create_user(db, telegram_id=555003)

    quotes_repo.add_quote(telegram_id, "Первая", _vector(0))
    quotes_repo.add_quote(telegram_id, "Вторая", _vector(1))

    deleted = quotes_repo.delete_all_quotes(telegram_id)
    assert deleted == 2
    assert quotes_repo.get_quote_count(telegram_id) == 0
    assert quotes_repo.semantic_search(telegram_id, _vector(0), top_k=3) == []
