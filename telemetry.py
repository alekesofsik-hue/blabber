"""
Telemetry / logging utilities for Blabber.

Goals:
 - Send structured logs to Better Stack (Logtail) if configured
 - Keep journald/stdout logs for local debugging
 - Never leak user messages or secrets to external logging

Env vars:
 - BETTERSTACK_SOURCE_TOKEN: Better Stack Logs source token
 - BETTERSTACK_INGEST_HOST: ingest host like "s123.eu-nbg-2.betterstackdata.com"
 - TELEMETRY_USER_HASH_SALT: optional salt to hash Telegram user ids
 - TELEMETRY_LEVEL: INFO/WARNING/...
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import Any, Dict, Optional


_SENSITIVE_KEY_RE = re.compile(
    r"(token|secret|api[_-]?key|authorization|password|cookie|session)",
    re.IGNORECASE,
)


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()


def user_id_hash(user_id: int) -> str:
    """
    Hashes Telegram user id for privacy. Stable within the same salt.
    """
    salt = os.getenv("TELEMETRY_USER_HASH_SALT", "")
    return _sha256_hex(f"{salt}:{user_id}")[:12]


def text_meta(text: str) -> Dict[str, Any]:
    """
    Returns non-sensitive metadata about text. Never returns the text itself.
    """
    return {
        "text_len": len(text or ""),
        "text_sha256_12": _sha256_hex(text or "")[:12],
    }


class RedactingFilter(logging.Filter):
    """
    Removes/Redacts sensitive fields from LogRecord before sending to external sinks.

    - Redacts any attribute whose key looks like secret/token/api_key
    - Truncates very large string fields (to avoid accidental log bloat)
    """

    def __init__(self, max_str_len: int = 500):
        super().__init__()
        self.max_str_len = max_str_len

    def _sanitize_value(self, v: Any) -> Any:
        if isinstance(v, str):
            if len(v) > self.max_str_len:
                return v[: self.max_str_len] + "...(truncated)"
            return v
        return v

    def filter(self, record: logging.LogRecord) -> bool:
        d = record.__dict__

        # Best-effort scrub: avoid leaking env-loaded secrets via extra.
        for k in list(d.keys()):
            if _SENSITIVE_KEY_RE.search(k or ""):
                d[k] = "[REDACTED]"
            else:
                d[k] = self._sanitize_value(d[k])

        # Also sanitize args if stringy
        try:
            if isinstance(record.args, dict):
                for k in list(record.args.keys()):
                    if _SENSITIVE_KEY_RE.search(k or ""):
                        record.args[k] = "[REDACTED]"
                    else:
                        record.args[k] = self._sanitize_value(record.args[k])
        except Exception:
            pass

        return True


def setup_telemetry(service_name: str = "blabber") -> logging.Logger:
    """
    Configure logger for both stdout/journald and Better Stack (optional).
    Safe to call multiple times.
    """
    level_name = os.getenv("TELEMETRY_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    logger.propagate = False

    # Base console handler (journald will capture stdout/stderr)
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    formatter = logging.Formatter(fmt=fmt)
    stream = logging.StreamHandler()
    stream.setLevel(level)
    stream.setFormatter(formatter)
    stream.addFilter(RedactingFilter())

    handlers = [stream]

    source_token = os.getenv("BETTERSTACK_SOURCE_TOKEN")
    ingest_host = os.getenv("BETTERSTACK_INGEST_HOST")
    if source_token and ingest_host:
        try:
            from logtail import LogtailHandler  # type: ignore

            bstack = LogtailHandler(
                source_token=source_token,
                host=f"https://{ingest_host}",
            )
            bstack.setLevel(level)
            bstack.addFilter(RedactingFilter())
            handlers.append(bstack)
        except Exception as e:
            # Fall back to stdout only (don't break the bot)
            logger.warning("Better Stack handler init failed: %s", e)

    logger.handlers = handlers
    logger.info("telemetry_ready", extra={"event": "telemetry_ready", "betterstack_enabled": bool(source_token and ingest_host)})
    return logger

