"""
GigaChat token utilities (OAuth).

This module is intentionally self-contained so it can be reused in other projects.

Public API:
    - get_gigachat_token()
    - get_gigachat_token_dict()
    - get_gigachat_token_info()
"""

from __future__ import annotations

import base64
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

load_dotenv()

GIGACHAT_TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"


def _parse_verify_ssl(verify_ssl: bool | None) -> bool:
    if verify_ssl is None:
        verify_ssl_str = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower()
        return verify_ssl_str in ("true", "1", "yes", "on")
    return bool(verify_ssl)


def _basic_auth(credentials: str) -> str:
    """
    Accepts:
      - 'client_id:client_secret'
      - 'Basic <base64>'
      - '<base64>'
    Returns '<base64>' (without 'Basic ').
    """
    if ":" in credentials and not credentials.startswith("Basic "):
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    if credentials.startswith("Basic "):
        return credentials.replace("Basic ", "", 1)
    return credentials


def _get_gigachat_token_direct(credentials: str, verify_ssl: bool = False) -> dict[str, Any]:
    """
    Low-level HTTP call to fetch token.
    Returns JSON dict with fields like: access_token, expires_at.
    """
    if httpx is None and requests is None:
        raise RuntimeError("Требуется библиотека httpx или requests.")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {_basic_auth(credentials)}",
    }
    data = {"scope": "GIGACHAT_API_PERS"}

    try:
        if httpx is not None:
            with httpx.Client(verify=verify_ssl, timeout=30.0) as client:
                r = client.post(GIGACHAT_TOKEN_URL, headers=headers, data=data)
                r.raise_for_status()
                return r.json()

        r = requests.post(
            GIGACHAT_TOKEN_URL,
            headers=headers,
            data=data,
            verify=verify_ssl,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:  # keep message stable
        raise Exception(f"Ошибка при получении токена GigaChat: {e}") from e


def get_gigachat_token(credentials: str | None = None, verify_ssl: bool | None = None) -> str:
    """
    Returns access token (string).
    """
    credentials = credentials or os.getenv("GIGACHAT_CREDENTIALS")
    if not credentials:
        raise ValueError(
            "GIGACHAT_CREDENTIALS не указан. "
            "Укажите его в параметре credentials или в переменной окружения GIGACHAT_CREDENTIALS"
        )

    verify_ssl_val = _parse_verify_ssl(verify_ssl)
    result = _get_gigachat_token_direct(credentials, verify_ssl_val)
    token = result.get("access_token")
    if not token:
        raise ValueError("Токен доступа не найден в ответе API")
    return token


def get_gigachat_token_dict(credentials: str | None = None, verify_ssl: bool | None = None) -> dict[str, Any]:
    """
    Returns full token response + computed fields:
      - expires_in_seconds
      - expires_at_datetime (UTC)
    """
    credentials = credentials or os.getenv("GIGACHAT_CREDENTIALS")
    if not credentials:
        raise ValueError(
            "GIGACHAT_CREDENTIALS не указан. "
            "Укажите его в параметре credentials или в переменной окружения GIGACHAT_CREDENTIALS"
        )

    verify_ssl_val = _parse_verify_ssl(verify_ssl)
    result = _get_gigachat_token_direct(credentials, verify_ssl_val)

    if not result.get("access_token"):
        raise ValueError("Токен доступа не найден в ответе API")

    expires_at_ms = result.get("expires_at")
    if expires_at_ms:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        expires_in_seconds = max(0, (expires_at_ms - now_ms) // 1000)
        expires_at_datetime = datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc)
        result["expires_in_seconds"] = int(expires_in_seconds)
        result["expires_at_datetime"] = expires_at_datetime
    else:
        result["expires_in_seconds"] = None
        result["expires_at_datetime"] = None

    return result


def get_gigachat_token_info(
    credentials: str | None = None, verify_ssl: bool | None = None
) -> tuple[str, int, datetime]:
    """
    Returns: (access_token, seconds_left, expires_at_datetime_utc)
    """
    token_data = get_gigachat_token_dict(credentials, verify_ssl)
    access_token = token_data["access_token"]
    expires_in_seconds = int(token_data.get("expires_in_seconds") or 0)
    expires_at_datetime = token_data.get("expires_at_datetime")
    if expires_at_datetime is None:
        raise ValueError("Не удалось определить время истечения токена")
    return access_token, expires_in_seconds, expires_at_datetime

