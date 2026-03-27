from __future__ import annotations

from database import get_connection
from repositories import user_repo
from services import history_day_memory_service


def _create_user(db, telegram_id: int = 664001) -> tuple[int, int]:
    with get_connection() as conn:
        role_id = conn.execute("SELECT id FROM roles WHERE name = 'user'").fetchone()["id"]
    user = user_repo.create(telegram_id, "histsvc_tester", "HistSvc", role_id)
    return telegram_id, user["id"]


def _vector(axis: int = 0, dim: int = 1536, value: float = 1.0) -> list[float]:
    vec = [0.0] * dim
    vec[axis] = value
    return vec


def test_save_user_message_skips_non_user_role(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, _user_db_id = _create_user(db)

    result = history_day_memory_service.save_user_message(
        telegram_id,
        role="assistant",
        text="Это ответ ассистента",
        scenario_tag="history_day_fact",
    )

    assert result["ok"] is True
    assert result["action"] == "skipped"


def test_save_user_message_skips_commands_and_empty_text(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, _user_db_id = _create_user(db, telegram_id=664002)

    empty_result = history_day_memory_service.save_user_message(
        telegram_id,
        role="user",
        text="   ",
        scenario_tag="history_day_fact",
    )
    command_result = history_day_memory_service.save_user_message(
        telegram_id,
        role="user",
        text="/historyday",
        scenario_tag="history_day_fact",
    )

    assert empty_result["action"] == "skipped"
    assert command_result["action"] == "skipped"


def test_save_user_message_falls_back_without_embeddings(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, _user_db_id = _create_user(db, telegram_id=664003)
    monkeypatch.setattr(history_day_memory_service.emb_svc, "is_available", lambda: False)

    result = history_day_memory_service.save_user_message(
        telegram_id,
        role="user",
        text="Что произошло 26 марта?",
        scenario_tag="history_day_fact",
    )

    assert result["ok"] is True
    assert result["action"] == "skipped"
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == "embeddings_unavailable"


def test_save_and_search_history_day_messages(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, _user_db_id = _create_user(db, telegram_id=664004)

    emb_map = {
        "Что произошло в этот день?": _vector(0),
        "Напомни, что было сегодня в истории": _vector(0, value=0.9),
    }
    monkeypatch.setattr(history_day_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(history_day_memory_service.emb_svc, "embed_single", lambda text: emb_map[text])

    save_result = history_day_memory_service.save_user_message(
        telegram_id,
        role="user",
        text="Что произошло в этот день?",
        scenario_tag="history_day_fact",
        command_name="historyday",
        event_date="03-26",
    )
    search_results = history_day_memory_service.search_relevant_messages(
        telegram_id,
        query="Напомни, что было сегодня в истории",
        scenario_tag="history_day_fact",
        top_k=3,
    )

    assert save_result["action"] == "saved"
    assert len(search_results) == 1
    assert search_results[0]["text"] == "Что произошло в этот день?"
    assert search_results[0]["score"] > 0


def test_search_relevant_messages_returns_empty_when_repo_fails(db, tmp_path, monkeypatch):
    monkeypatch.setenv("LANCEDB_PATH", str(tmp_path / "lancedb"))
    telegram_id, _user_db_id = _create_user(db, telegram_id=664005)
    monkeypatch.setattr(history_day_memory_service.emb_svc, "is_available", lambda: True)
    monkeypatch.setattr(history_day_memory_service.emb_svc, "embed_single", lambda text: _vector(0))

    def _boom(**kwargs):
        raise RuntimeError("search unavailable")

    monkeypatch.setattr(history_day_memory_service.memory_repo, "search_by_vector", _boom)
    results = history_day_memory_service.search_relevant_messages(
        telegram_id,
        query="Что было сегодня в истории?",
        scenario_tag="history_day_fact",
    )

    assert results == []
