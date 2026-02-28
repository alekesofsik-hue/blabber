"""
Unit tests for repositories/config_repo.py.
"""

from __future__ import annotations

import pytest
from repositories import config_repo


# ── upsert / get ─────────────────────────────────────────────────────────────

def test_upsert_and_get(db):
    config_repo.upsert("test_key", "hello", "str", "general", "A test key")
    row = config_repo.get("test_key")
    assert row is not None
    assert row["key"] == "test_key"
    assert row["value"] == "hello"
    assert row["value_type"] == "str"


def test_get_nonexistent_returns_none(db):
    assert config_repo.get("no_such_key") is None


def test_upsert_overwrites_existing(db):
    config_repo.upsert("dup_key", "original", "str", "general")
    config_repo.upsert("dup_key", "updated", "str", "general")

    row = config_repo.get("dup_key")
    assert row["value"] == "updated"


def test_upsert_int_type(db):
    config_repo.upsert("max_tokens", "5000", "int", "limits")
    row = config_repo.get("max_tokens")
    assert row["value_type"] == "int"
    assert row["value"] == "5000"


def test_upsert_bool_type(db):
    config_repo.upsert("maintenance_mode", "true", "bool", "system")
    row = config_repo.get("maintenance_mode")
    assert row["value"] == "true"


def test_upsert_json_type(db):
    config_repo.upsert(
        "models_enabled",
        '{"gigachat":true,"ollama":false}',
        "json",
        "models",
    )
    row = config_repo.get("models_enabled")
    assert row["value_type"] == "json"


def test_upsert_secret_flag(db):
    config_repo.upsert("api_secret", "tok123", "str", "secrets", is_secret=True)
    row = config_repo.get("api_secret")
    assert row["is_secret"] == 1


# ── get_all ───────────────────────────────────────────────────────────────────

def test_get_all_returns_seeded_rows(db):
    """Migration 002 seeds multiple rows; get_all should return them."""
    rows = config_repo.get_all()
    keys = {r["key"] for r in rows}
    assert "default_model" in keys
    assert "tts_max_chars" in keys


def test_get_all_category_filter(db):
    config_repo.upsert("cat_a_1", "v1", "str", "cat_a")
    config_repo.upsert("cat_a_2", "v2", "str", "cat_a")
    config_repo.upsert("cat_b_1", "v3", "str", "cat_b")

    rows_a = config_repo.get_all(category="cat_a")
    assert all(r["category"] == "cat_a" for r in rows_a)
    assert len(rows_a) == 2


# ── delete ───────────────────────────────────────────────────────────────────

def test_delete_existing(db):
    config_repo.upsert("to_delete", "bye", "str", "general")
    assert config_repo.delete("to_delete") is True
    assert config_repo.get("to_delete") is None


def test_delete_nonexistent_returns_false(db):
    assert config_repo.delete("ghost_key") is False
