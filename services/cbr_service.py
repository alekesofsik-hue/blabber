"""
CBR (Банк России) exchange rate service.

Fetches the official USD/RUB rate from the CBR XML API.
Rate is cached for CBR_CACHE_TTL_SECONDS to avoid hammering the API.
Falls back to a hardcoded fallback rate if the API is unavailable.
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger("blabber")

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
CBR_CACHE_TTL_SECONDS = 3600  # 1 hour
CBR_FALLBACK_RATE = 90.0      # fallback if API unreachable

_cached_rate: float | None = None
_cached_at: float = 0.0


def get_usd_rub_rate() -> float:
    """
    Return current USD/RUB exchange rate from CBR.
    Uses an in-memory cache with TTL.
    """
    global _cached_rate, _cached_at

    now = time.monotonic()
    if _cached_rate is not None and (now - _cached_at) < CBR_CACHE_TTL_SECONDS:
        return _cached_rate

    try:
        resp = requests.get(CBR_URL, timeout=5)
        resp.raise_for_status()
        # CBR returns Windows-1251 encoded XML
        resp.encoding = "windows-1251"
        root = ET.fromstring(resp.text)
        for valute in root.findall("Valute"):
            char_code = valute.findtext("CharCode", "")
            if char_code == "USD":
                nominal = int(valute.findtext("Nominal", "1"))
                value_str = (valute.findtext("Value", "0") or "0").replace(",", ".")
                rate = float(value_str) / nominal
                _cached_rate = rate
                _cached_at = now
                logger.info(
                    "cbr_rate_fetched",
                    extra={"event": "cbr_rate_fetched", "usd_rub": round(rate, 2)},
                )
                return rate
    except Exception as exc:
        logger.warning(
            "cbr_rate_fetch_failed",
            extra={"event": "cbr_rate_fetch_failed", "error": str(exc)},
        )

    return _cached_rate if _cached_rate is not None else CBR_FALLBACK_RATE


def format_cost_rub(cost_usd: float) -> str:
    """
    Convert USD cost to RUB string for display, e.g. '0.12 ₽'.
    Returns empty string if cost is zero or negligible.
    """
    if cost_usd <= 0:
        return ""
    rate = get_usd_rub_rate()
    cost_rub = cost_usd * rate
    if cost_rub < 0.001:
        return ""
    if cost_rub < 0.01:
        return f"~{cost_rub:.4f} ₽"
    return f"~{cost_rub:.2f} ₽"
