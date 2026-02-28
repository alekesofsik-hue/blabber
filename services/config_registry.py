"""
ConfigRegistry — Singleton with in-memory cache for dynamic configuration.

Loads from DB on startup, serves from cache. Optional TTL reload.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any

from repositories.config_repo import get_all, upsert

logger = logging.getLogger("blabber")

_VALUE_CASTERS = {
    "str": str,
    "int": lambda v: int(v) if v is not None and str(v).strip() != "" else 0,
    "float": lambda v: float(v) if v is not None and str(v).strip() != "" else 0.0,
    "bool": lambda v: str(v).lower() in ("true", "1", "yes", "on"),
    "json": json.loads,
}


def _cast(value: str, value_type: str) -> Any:
    """Deserialize string value to native type."""
    if value is None:
        return None
    caster = _VALUE_CASTERS.get(value_type, str)
    try:
        return caster(value)
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        logger.warning(
            "config_cast_failed",
            extra={"event": "config_cast_failed", "value": str(value)[:50], "value_type": value_type, "error": str(e)},
        )
        return value


class ConfigRegistry:
    """
    Singleton with in-memory cache. Thread-safe.
    """

    _instance: ConfigRegistry | None = None
    _lock = threading.Lock()

    def __new__(cls) -> ConfigRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._cache: dict[str, Any] = {}
        self._raw: dict[str, dict] = {}
        self._ttl: int = 300
        self._last_load: float = 0
        self._rw_lock = threading.RLock()
        self._initialized = True

    def load(self, db_rows: list[dict[str, Any]] | None = None) -> None:
        """
        Full reload from DB. If db_rows is None, fetches from config_repo.
        """
        with self._rw_lock:
            rows = db_rows if db_rows is not None else get_all()
            self._cache.clear()
            self._raw.clear()
            for row in rows:
                key = row["key"]
                self._raw[key] = dict(row)
                self._cache[key] = _cast(row["value"], row.get("value_type", "str"))
            self._last_load = time.time()
            logger.debug(
                "config_registry_loaded",
                extra={"event": "config_registry_loaded", "keys_count": len(self._cache)},
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (0 DB hits)."""
        self._maybe_reload()
        with self._rw_lock:
            if key in self._cache:
                return self._cache[key]
            return default

    def set(
        self,
        key: str,
        value: Any,
        value_type: str = "str",
        category: str = "general",
        description: str | None = None,
        is_secret: bool = False,
        updated_by: int | None = None,
    ) -> None:
        """Write to cache and DB atomically."""
        str_value = str(value).lower() if isinstance(value, bool) else str(value)
        if value_type == "json" and not isinstance(value, str):
            str_value = json.dumps(value)
        with self._rw_lock:
            self._cache[key] = _cast(str_value, value_type)
            self._raw[key] = {
                "key": key,
                "value": str_value,
                "value_type": value_type,
                "category": category,
            }
            upsert(key, str_value, value_type, category, description, is_secret, updated_by)

    def all(self, category: str | None = None) -> dict[str, Any]:
        """All params, optionally filtered by category."""
        self._maybe_reload()
        with self._rw_lock:
            if category is None:
                return dict(self._cache)
            return {k: v for k, v in self._cache.items() if self._raw.get(k, {}).get("category") == category}

    def _maybe_reload(self) -> None:
        """TTL-based reload — safety net if DB was changed directly."""
        with self._rw_lock:
            if time.time() - self._last_load > self._ttl:
                try:
                    self.load(None)
                except Exception as e:
                    logger.warning(
                        "config_registry_reload_failed",
                        extra={"event": "config_registry_reload_failed", "error": str(e)},
                    )


# Global instance
_registry: ConfigRegistry | None = None


def get_config_registry() -> ConfigRegistry:
    """Get or create global ConfigRegistry instance."""
    global _registry
    if _registry is None:
        _registry = ConfigRegistry()
    return _registry


def get_setting(key: str, default: Any = None, env_key: str | None = None) -> Any:
    """
    Single entry point for config. Priority: ConfigRegistry (DB) → os.environ → default.

    Args:
        key: Config key (used for registry and env if env_key not set)
        default: Fallback if not found
        env_key: Optional env var name (e.g. OLLAMA_MODEL when key=ollama_model)
    """
    import os

    registry = get_config_registry()
    value = registry.get(key)
    if value is not None:
        return value
    env_name = env_key or key
    env_val = os.environ.get(env_name)
    if env_val is not None:
        return env_val
    return default
