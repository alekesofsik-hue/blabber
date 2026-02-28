"""
Admin rate limiter — prevents abuse if an admin account is compromised.

Limits each Telegram user to at most MAX_ADMIN_COMMANDS commands
per WINDOW_SECONDS sliding window.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque

logger = logging.getLogger("blabber")

MAX_ADMIN_COMMANDS: int = 10
WINDOW_SECONDS: int = 60

# {telegram_id: deque of timestamps}
_counters: dict[int, deque] = {}
_lock = threading.Lock()


def is_rate_limited(telegram_id: int) -> bool:
    """
    Return True if telegram_id has exceeded the admin command rate limit.

    Uses a sliding window: keeps only timestamps within the last WINDOW_SECONDS.
    Thread-safe.
    """
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS

    with _lock:
        if telegram_id not in _counters:
            _counters[telegram_id] = deque()

        dq = _counters[telegram_id]

        # Drop old timestamps outside the window
        while dq and dq[0] < cutoff:
            dq.popleft()

        if len(dq) >= MAX_ADMIN_COMMANDS:
            logger.warning(
                "admin_rate_limited",
                extra={
                    "event": "admin_rate_limited",
                    "telegram_id": telegram_id,
                    "count_in_window": len(dq),
                    "window_seconds": WINDOW_SECONDS,
                },
            )
            return True

        dq.append(now)
        return False


def reset(telegram_id: int) -> None:
    """Clear rate limit counters for a user (e.g. in tests or after unban)."""
    with _lock:
        _counters.pop(telegram_id, None)


def get_retry_after(telegram_id: int) -> int:
    """
    Seconds until the oldest recorded call leaves the window.
    Returns 0 if not rate-limited.
    """
    now = time.monotonic()
    with _lock:
        dq = _counters.get(telegram_id)
        if not dq:
            return 0
        oldest = dq[0]
        retry = int(WINDOW_SECONDS - (now - oldest)) + 1
        return max(0, retry)
