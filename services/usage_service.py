"""
Usage service — logging and analytics for LLM calls.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from repositories.usage_repo import insert as usage_insert
from repositories.user_repo import get_by_telegram_id


def log_request(
    telegram_id: int,
    provider: str,
    model: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost: float = 0.0,
    duration_ms: int | None = None,
    success: bool = True,
    error_text: str | None = None,
) -> None:
    """
    Log an LLM request to usage_logs. Requires user to exist.
    """
    user = get_by_telegram_id(telegram_id)
    if not user:
        return
    user_id = user["id"]
    usage_insert(
        user_id=user_id,
        provider=provider,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost=cost,
        duration_ms=duration_ms,
        success=success,
        error_text=error_text,
    )


def get_daily_report() -> dict[str, Any]:
    """Summary for today: total requests, tokens, cost, by provider."""
    from repositories.usage_repo import get_requests_count, get_provider_breakdown

    now = datetime.utcnow()
    today_start = now.strftime("%Y-%m-%d 00:00:00")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    requests = get_requests_count(today_start, now_str)
    breakdown = get_provider_breakdown(today_start, now_str)

    from database import get_connection

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(tokens_in) + SUM(tokens_out), 0) AS tokens,
                   COALESCE(SUM(cost_usd), 0.0) AS cost
            FROM usage_logs
            WHERE created_at >= ? AND created_at < ?
            """,
            (today_start, now_str),
        ).fetchone()
        tokens = row["tokens"] if row else 0
        cost = row["cost"] if row else 0.0

    return {
        "requests": requests,
        "tokens": tokens,
        "cost": cost,
        "by_provider": breakdown,
    }


def get_user_report(telegram_id: int, days: int = 7) -> dict[str, Any]:
    """Report for a user over the last N days."""
    from database import get_connection

    user = get_by_telegram_id(telegram_id)
    if not user:
        return {"error": "user_not_found"}

    now = datetime.utcnow()
    start = (now - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
    end = now.strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS requests,
                   COALESCE(SUM(tokens_in) + SUM(tokens_out), 0) AS tokens,
                   COALESCE(SUM(cost_usd), 0.0) AS cost
            FROM usage_logs
            WHERE user_id = ? AND created_at >= ? AND created_at < ?
            """,
            (user["id"], start, end),
        ).fetchone()

    return {
        "telegram_id": telegram_id,
        "username": user.get("username"),
        "requests": row["requests"] if row else 0,
        "tokens": row["tokens"] if row else 0,
        "cost": row["cost"] if row else 0.0,
        "days": days,
    }
