"""
Usage repository — CRUD and aggregations for usage_logs table.
"""

from __future__ import annotations

from typing import Any

from database import get_connection


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()} if hasattr(row, "keys") else dict(row)


def insert(
    user_id: int,
    provider: str,
    model: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost: float = 0.0,
    duration_ms: int | None = None,
    success: bool = True,
    error_text: str | None = None,
) -> None:
    """Insert usage log entry (user_id = users.id)."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO usage_logs (user_id, provider, model, tokens_in, tokens_out, cost_usd, duration_ms, success, error_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, provider, model, tokens_in, tokens_out, cost, duration_ms or 0, 1 if success else 0, error_text),
        )


def get_user_usage_today(telegram_id: int) -> dict[str, Any]:
    """Get today's usage for user (tokens, requests, cost). Resets at midnight UTC."""
    with get_connection() as conn:
        from datetime import datetime
        now = datetime.utcnow()
        today_start = now.strftime("%Y-%m-%d 00:00:00")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        row = conn.execute(
            """
            SELECT COALESCE(SUM(ul.tokens_in) + SUM(ul.tokens_out), 0) AS tokens,
                   COUNT(*) AS requests,
                   COALESCE(SUM(ul.cost_usd), 0.0) AS cost
            FROM usage_logs ul
            JOIN users u ON ul.user_id = u.id
            WHERE u.telegram_id = ? AND ul.created_at >= ? AND ul.created_at < ?
            """,
            (telegram_id, today_start, now_str),
        ).fetchone()
        if row:
            return {"tokens": row["tokens"] or 0, "requests": row["requests"] or 0, "cost": row["cost"] or 0.0}
    return {"tokens": 0, "requests": 0, "cost": 0.0}


def get_requests_count(start: str, end: str) -> int:
    """Count requests in period (datetime strings)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM usage_logs WHERE created_at >= ? AND created_at < ?",
            (start, end),
        ).fetchone()
        return row["cnt"] if row else 0


def get_provider_breakdown(start: str, end: str) -> list[dict[str, Any]]:
    """Requests per provider in period."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT provider, COUNT(*) AS cnt
            FROM usage_logs
            WHERE created_at >= ? AND created_at < ?
            GROUP BY provider
            ORDER BY cnt DESC
            """,
            (start, end),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def get_top_users(limit: int = 5, start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
    """Top users by request count. Optional date filter."""
    with get_connection() as conn:
        if start and end:
            rows = conn.execute(
                """
                SELECT u.telegram_id, u.username, u.first_name, COUNT(*) AS req_count
                FROM usage_logs ul
                JOIN users u ON ul.user_id = u.id
                WHERE ul.created_at >= ? AND ul.created_at < ?
                GROUP BY ul.user_id
                ORDER BY req_count DESC
                LIMIT ?
                """,
                (start, end, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT u.telegram_id, u.username, u.first_name, COUNT(*) AS req_count
                FROM usage_logs ul
                JOIN users u ON ul.user_id = u.id
                GROUP BY ul.user_id
                ORDER BY req_count DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [_row_to_dict(r) for r in rows]
