"""
Unit tests for services/config_registry.py — caching, cast, TTL, graceful fallback.
"""

from __future__ import annotations

import pytest

from services.config_registry import ConfigRegistry, _cast, get_setting


# ── _cast ─────────────────────────────────────────────────────────────────────

class TestCast:
    def test_str(self):
        assert _cast("hello", "str") == "hello"

    def test_int(self):
        assert _cast("42", "int") == 42

    def test_int_empty_returns_zero(self):
        assert _cast("", "int") == 0

    def test_float(self):
        assert _cast("3.14", "float") == pytest.approx(3.14)

    def test_bool_true_variants(self):
        for v in ("true", "1", "yes", "on", "True", "YES"):
            assert _cast(v, "bool") is True, f"Expected True for {v!r}"

    def test_bool_false_variants(self):
        for v in ("false", "0", "no", "off", "FALSE"):
            assert _cast(v, "bool") is False, f"Expected False for {v!r}"

    def test_json(self):
        result = _cast('{"key": 1}', "json")
        assert result == {"key": 1}

    def test_json_list(self):
        result = _cast('[1,2,3]', "json")
        assert result == [1, 2, 3]

    def test_invalid_int_returns_raw(self):
        # Should log warning and return original value, not crash
        result = _cast("not_a_number", "int")
        assert result == "not_a_number"

    def test_invalid_json_returns_raw(self):
        result = _cast("{bad json}", "json")
        assert result == "{bad json}"

    def test_none_returns_none(self):
        assert _cast(None, "str") is None

    def test_unknown_type_uses_str(self):
        assert _cast("hello", "weird_type") == "hello"


# ── ConfigRegistry ───────────────────────────────────────────────────────────

class TestConfigRegistry:

    def test_singleton(self):
        a = ConfigRegistry()
        b = ConfigRegistry()
        assert a is b

    def test_load_from_rows(self, db):
        reg = ConfigRegistry()
        reg.load([
            {"key": "foo", "value": "bar", "value_type": "str", "category": "test"},
            {"key": "num", "value": "10", "value_type": "int", "category": "test"},
        ])
        assert reg.get("foo") == "bar"
        assert reg.get("num") == 10

    def test_get_missing_key_returns_default(self, db):
        reg = ConfigRegistry()
        reg.load([])
        assert reg.get("nonexistent", "fallback") == "fallback"

    def test_set_updates_cache_and_db(self, db):
        reg = ConfigRegistry()
        reg.load([])
        reg.set("new_key", "new_value", "str", "general")
        assert reg.get("new_key") == "new_value"

        # Verify persisted in DB
        from repositories.config_repo import get as cfg_get
        row = cfg_get("new_key")
        assert row is not None
        assert row["value"] == "new_value"

    def test_set_bool_serialized_correctly(self, db):
        reg = ConfigRegistry()
        reg.load([])
        reg.set("flag", True, "bool", "system")
        # Cache should hold native bool
        assert reg.get("flag") is True

    def test_set_json_serialized_correctly(self, db):
        reg = ConfigRegistry()
        reg.load([])
        reg.set("mapping", {"a": 1}, "json", "test")
        assert reg.get("mapping") == {"a": 1}

    def test_all_no_category(self, db):
        reg = ConfigRegistry()
        reg.load([
            {"key": "x", "value": "1", "value_type": "int", "category": "c1"},
            {"key": "y", "value": "2", "value_type": "int", "category": "c2"},
        ])
        result = reg.all()
        assert "x" in result
        assert "y" in result

    def test_all_with_category_filter(self, db):
        reg = ConfigRegistry()
        reg.load([
            {"key": "a", "value": "1", "value_type": "int", "category": "alpha"},
            {"key": "b", "value": "2", "value_type": "int", "category": "beta"},
        ])
        alpha = reg.all(category="alpha")
        assert "a" in alpha
        assert "b" not in alpha

    def test_reload_from_db(self, db):
        """set() persists; a fresh registry.load(None) sees it."""
        reg = ConfigRegistry()
        reg.load([])
        reg.set("persist_me", "yes", "str")

        # Reset singleton and reload from DB
        ConfigRegistry._instance = None
        import services.config_registry as cr_mod
        cr_mod._registry = None

        from services.config_registry import ConfigRegistry as CR2
        reg2 = CR2()
        reg2.load(None)  # loads from DB
        assert reg2.get("persist_me") == "yes"

    def test_ttl_reload_on_stale(self, db, monkeypatch):
        """When cache is stale (last_load=0), _maybe_reload is triggered."""
        import time
        reg = ConfigRegistry()
        reg.load([])
        reg._last_load = 0  # Force stale

        from repositories import config_repo
        config_repo.upsert("ttl_key", "ttl_val", "str")

        # Access triggers _maybe_reload
        result = reg.get("ttl_key", "NOT_FOUND")
        assert result == "ttl_val"

    def test_load_db_failure_does_not_crash(self, db, monkeypatch):
        """If DB is unavailable during _maybe_reload, registry keeps old values."""
        reg = ConfigRegistry()
        reg.load([{"key": "safe_key", "value": "safe_val", "value_type": "str", "category": "t"}])
        reg._last_load = 0  # Force stale

        def boom():
            raise RuntimeError("DB is down")

        monkeypatch.setattr("services.config_registry.get_all", lambda *a, **kw: boom())
        # Should not raise; returns cached value
        assert reg.get("safe_key") == "safe_val"


# ── get_setting ───────────────────────────────────────────────────────────────

class TestGetSetting:

    def test_returns_db_value_first(self, db):
        from services.config_registry import ConfigRegistry as CR, get_config_registry
        reg = CR()
        reg.load([{"key": "prio", "value": "db_val", "value_type": "str", "category": "t"}])
        import services.config_registry as cr_mod
        cr_mod._registry = reg

        result = get_setting("prio", "fallback", env_key="PRIO_ENV")
        assert result == "db_val"

    def test_falls_back_to_env(self, db, monkeypatch):
        from services.config_registry import ConfigRegistry as CR
        reg = CR()
        reg.load([])
        import services.config_registry as cr_mod
        cr_mod._registry = reg

        monkeypatch.setenv("MY_VAR", "env_val")
        result = get_setting("missing_key", "fallback", env_key="MY_VAR")
        assert result == "env_val"

    def test_falls_back_to_default(self, db):
        from services.config_registry import ConfigRegistry as CR
        reg = CR()
        reg.load([])
        import services.config_registry as cr_mod
        cr_mod._registry = reg

        result = get_setting("totally_missing", default="def_val")
        assert result == "def_val"
