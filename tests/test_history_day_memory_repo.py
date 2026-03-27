from __future__ import annotations

from database import get_connection
from repositories import history_day_memory_repo, user_repo


def _create_user(db, telegram_id: int = 665001) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "histmem_tester", "HistMem", role_id)
    return telegram_id, user["id"]


def _vector(axis: int = 0, dim: int = history_day_memory_repo.EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = 1.0
    return vec


def test_upsert_and_search_history_day_memory(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    _telegram_id, user_db_id = _create_user(db)

    written = history_day_memory_repo.upsert_message(
        user_db_id=user_db_id,
        source_id="msg-101",
        text="Что произошло в этот день?",
        vector=_vector(0),
        scenario_tag="history_day_fact",
        created_at="2026-03-26 10:00:00",
        command_name="historyday",
        source_kind="user_message",
        event_date="03-26",
    )

    assert written is True

    results = history_day_memory_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(0),
        top_k=3,
    )
    assert len(results) == 1
    assert results[0]["source_id"] == "msg-101"
    assert results[0]["scenario_tag"] == "history_day_fact"
    assert results[0]["text"] == "Что произошло в этот день?"


def test_search_history_day_memory_filters_by_user(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    _telegram_id_a, user_db_id_a = _create_user(db, telegram_id=665002)
    _telegram_id_b, user_db_id_b = _create_user(db, telegram_id=665003)

    history_day_memory_repo.upsert_message(
        user_db_id=user_db_id_a,
        source_id="msg-a",
        text="Первый пользователь",
        vector=_vector(0),
        scenario_tag="history_day_fact",
        created_at="2026-03-26 10:00:00",
    )
    history_day_memory_repo.upsert_message(
        user_db_id=user_db_id_b,
        source_id="msg-b",
        text="Второй пользователь",
        vector=_vector(0),
        scenario_tag="history_day_fact",
        created_at="2026-03-26 10:00:01",
    )

    results = history_day_memory_repo.search_by_vector(
        user_db_id=user_db_id_a,
        query_vector=_vector(0),
        top_k=5,
    )
    assert len(results) == 1
    assert results[0]["source_id"] == "msg-a"


def test_search_history_day_memory_filters_by_scenario_tag(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    _telegram_id, user_db_id = _create_user(db, telegram_id=665004)

    history_day_memory_repo.upsert_messages(
        user_db_id=user_db_id,
        items=[
            {
                "source_id": "fact-1",
                "text": "Факт дня",
                "vector": _vector(0),
                "scenario_tag": "history_day_fact",
                "created_at": "2026-03-26 10:00:00",
                "command_name": "historyday",
                "source_kind": "user_message",
                "event_date": "03-26",
            },
            {
                "source_id": "followup-1",
                "text": "А напомни год",
                "vector": _vector(0),
                "scenario_tag": "history_day_followup",
                "created_at": "2026-03-26 10:05:00",
                "command_name": "historyday_ask",
                "source_kind": "user_message",
                "event_date": "03-26",
            },
        ],
    )

    results = history_day_memory_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(0),
        top_k=5,
        scenario_tag="history_day_followup",
    )
    assert len(results) == 1
    assert results[0]["source_id"] == "followup-1"


def test_delete_by_source_ids_removes_only_target_rows(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    _telegram_id, user_db_id = _create_user(db, telegram_id=665005)

    history_day_memory_repo.upsert_messages(
        user_db_id=user_db_id,
        items=[
            {
                "source_id": "msg-1",
                "text": "Первое сообщение",
                "vector": _vector(0),
                "scenario_tag": "history_day_fact",
                "created_at": "2026-03-26 10:00:00",
            },
            {
                "source_id": "msg-2",
                "text": "Второе сообщение",
                "vector": _vector(1),
                "scenario_tag": "history_day_fact",
                "created_at": "2026-03-26 10:01:00",
            },
        ],
    )

    history_day_memory_repo.delete_by_source_ids(user_db_id=user_db_id, source_ids=["msg-1"])

    first = history_day_memory_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(0),
        top_k=5,
    )
    second = history_day_memory_repo.search_by_vector(
        user_db_id=user_db_id,
        query_vector=_vector(1),
        top_k=5,
    )

    assert all(row["source_id"] != "msg-1" for row in first)
    assert any(row["source_id"] == "msg-2" for row in second)
