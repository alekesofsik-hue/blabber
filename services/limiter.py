"""
Limiter — check and track daily token/request limits per user.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from repositories.user_repo import get_by_telegram_id


def reset_if_needed(telegram_id: int) -> None:
    """
    Lazy reset: if now > limits_reset_at, reset tokens_used_today and requests_today,
    and set limits_reset_at = now + 24h.
    """
    from database import get_connection

    user = get_by_telegram_id(telegram_id)
    if not user:
        return
    reset_at = user.get("limits_reset_at")
    if not reset_at:
        return
    # Parse SQLite datetime (YYYY-MM-DD HH:MM:SS)
    try:
        if isinstance(reset_at, str):
            reset_dt = datetime.strptime(reset_at[:19], "%Y-%m-%d %H:%M:%S")
        else:
            return
    except (ValueError, TypeError):
        return
    now = datetime.utcnow()
    if now >= reset_dt:
        next_reset = (now + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET tokens_used_today = 0, requests_today = 0, limits_reset_at = ?, updated_at = datetime('now')
                WHERE telegram_id = ?
                """,
                (next_reset, telegram_id),
            )


def check_limits(telegram_id: int) -> tuple[bool, str | None]:
    """
    Check if user is within limits. Returns (allowed, reason).
    reason is None if allowed, else a message for the user.
    """
    reset_if_needed(telegram_id)
    user = get_by_telegram_id(telegram_id)
    if not user:
        return True, None  # Not registered, allow (will be created on first message)
    tokens = user.get("tokens_used_today") or 0
    requests = user.get("requests_today") or 0
    _tl = user.get("daily_token_limit")
    _rl = user.get("daily_request_limit")
    token_limit = _tl if _tl is not None else 50000
    req_limit = _rl if _rl is not None else 100

    if tokens >= token_limit:
        reset_at = user.get("limits_reset_at", "")
        return False, _format_limit_message(tokens, token_limit, requests, req_limit, reset_at)
    if requests >= req_limit:
        reset_at = user.get("limits_reset_at", "")
        return False, _format_limit_message(tokens, token_limit, requests, req_limit, reset_at)
    return True, None


def _format_limit_message(
    tokens: int, token_limit: int, requests: int, req_limit: int, reset_at: str
) -> str:
    """Format user-facing limit exceeded message with time until reset."""
    try:
        if isinstance(reset_at, str):
            reset_dt = datetime.strptime(reset_at[:19], "%Y-%m-%d %H:%M:%S")
        else:
            reset_dt = datetime.utcnow()
    except (ValueError, TypeError):
        reset_dt = datetime.utcnow()
    now = datetime.utcnow()
    delta = reset_dt - now
    hours = max(0, int(delta.total_seconds() // 3600))
    mins = max(0, int((delta.total_seconds() % 3600) // 60))
    time_str = f"{hours}ч {mins}м" if hours or mins else "менее минуты"
    return (
        f"⏳ Лимит исчерпан. Осталось до сброса: {time_str}\n\n"
        f"Использовано: {tokens} токенов из {token_limit}, {requests} запросов из {req_limit}"
    )


def increment_usage(telegram_id: int, tokens_used: int) -> None:
    """Increment user's tokens_used_today and requests_today."""
    from database import get_connection

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET tokens_used_today = tokens_used_today + ?, requests_today = requests_today + 1,
                updated_at = datetime('now')
            WHERE telegram_id = ?
            """,
            (tokens_used, telegram_id),
        )


def get_remaining(telegram_id: int) -> dict[str, int]:
    """Get remaining token and request limits."""
    reset_if_needed(telegram_id)
    user = get_by_telegram_id(telegram_id)
    if not user:
        return {"tokens": 50000, "requests": 100}
    tokens_used = user.get("tokens_used_today") or 0
    requests_used = user.get("requests_today") or 0
    _tl = user.get("daily_token_limit")
    _rl = user.get("daily_request_limit")
    token_limit = _tl if _tl is not None else 50000
    req_limit = _rl if _rl is not None else 100
    return {
        "tokens": max(0, token_limit - tokens_used),
        "requests": max(0, req_limit - requests_used),
    }
