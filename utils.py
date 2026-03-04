"""
Утилиты для работы с LLM API: OpenRouter, GigaChat, Yandex GPT, Ollama и DeepSeek R1.

Этот модуль обеспечивает обратную совместимость с существующим кодом бота.
Внутри используются универсальные модули из llm_providers.

Для новых проектов рекомендуется использовать модули из llm_providers напрямую:
    from llm_providers.openrouter import get_response
    from llm_providers.gigachat import get_response
    from llm_providers.yandexgpt import get_response
    from llm_providers.ollama import get_response
"""

import os
import time
import logging
from dotenv import load_dotenv

from llm_providers.openrouter import get_response as openrouter_get_response
from llm_providers.gigachat import get_response as gigachat_get_response
from llm_providers.yandexgpt import get_response as yandexgpt_get_response
from llm_providers.ollama import get_response as ollama_get_response
from llm_providers.openai import get_response as openai_get_response

load_dotenv()

DEFAULT_SYSTEM_MESSAGE = (
    "Ты — балабол, любишь много говорить, трепаться и болтать. "
    "Ты не всегда прав, можешь давать пустую болтовню, но всегда дружелюбен и шутлив. "
    "Отвечай многословно, с юмором, иногда отвлекаясь на разные темы."
)

# ── Cost price table ──────────────────────────────────────────────────────────
# (input_price_per_1k, output_price_per_1k) in USD
# Only populated for providers where real usage tokens are available via API.
_PRICE_TABLE: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o-mini":    (0.00015,  0.00060),
    "gpt-4o":         (0.00250,  0.01000),
    "gpt-4-turbo":    (0.01000,  0.03000),
    # OpenRouter / DeepSeek
    "deepseek/deepseek-chat": (0.00014, 0.00028),
    "deepseek/deepseek-r1":   (0.00055, 0.00219),
}

_MODEL_KEY_FOR_PRICE = {
    "openai":     "gpt-4o-mini",       # default; real model from config may differ
    "openrouter": "deepseek/deepseek-chat",
    "reasoning":  "deepseek/deepseek-r1",
}


def _estimate_tokens(text: str) -> int:
    """Approximate token count (chars / 4)."""
    return max(0, len(text or "") // 4)


def _calc_cost(provider: str, tokens_in: int, tokens_out: int) -> float:
    """Return estimated cost_usd for a request. Returns 0.0 for unknown providers."""
    price_key = _MODEL_KEY_FOR_PRICE.get(provider)
    if not price_key:
        return 0.0
    in_price, out_price = _PRICE_TABLE.get(price_key, (0.0, 0.0))
    return (tokens_in * in_price + tokens_out * out_price) / 1000.0


def get_chat_response(
    user_message: str,
    model: str = 'openrouter',
    *,
    history: list | None = None,
    system_message: str | None = None,
    request_id: str | None = None,
    user_id_hash: str | None = None,
    telegram_id: int | None = None,
) -> str:
    """
    Получить ответ от выбранной модели с заданным стилем "балабола".

    Args:
        user_message: Сообщение от пользователя
        model: Модель для генерации
        history: Список {"role", "content"} — история диалога для контекста (None = без контекста)
        system_message: Системный промпт (если None — используется DEFAULT_SYSTEM_MESSAGE)
        request_id: ID запроса для логирования
        user_id_hash: Хеш telegram_id для логирования
        telegram_id: Telegram ID для записи usage

    Returns:
        Ответ от модели

    Raises:
        ValueError: Если указана неизвестная модель
        Exception: При ошибке обращения к API
    """
    system_message = system_message or DEFAULT_SYSTEM_MESSAGE
    logger = logging.getLogger("blabber")
    t0 = time.monotonic()
    ctx = history or []

    logger.info(
        "llm_request_started",
        extra={
            "event": "llm_request_started",
            "request_id": request_id,
            "user_id_hash": user_id_hash,
            "provider": model,
            "context_turns": len(ctx) // 2 if ctx else 0,
        },
    )

    try:
        # usage_out collects real token counts from providers that support it
        usage_out: dict = {}

        if model == 'gigachat':
            result = gigachat_get_response(
                message=user_message,
                system_message=system_message,
                history=ctx,
            )
        elif model == 'yandexgpt':
            result = yandexgpt_get_response(
                message=user_message,
                system_message=system_message,
                history=ctx,
            )
        elif model == 'ollama':
            result = ollama_get_response(
                message=user_message,
                system_message=system_message,
                history=ctx,
            )
        elif model == 'openai':
            result = openai_get_response(
                message=user_message,
                system_message=system_message,
                history=ctx,
                usage_out=usage_out,
            )
        elif model == 'openrouter':
            result = openrouter_get_response(
                message=user_message,
                system_message=system_message,
                history=ctx,
                usage_out=usage_out,
            )
        elif model == 'reasoning':
            result = openrouter_get_response(
                message=user_message,
                system_message=system_message,
                history=ctx,
                model="deepseek/deepseek-r1",
                temperature=0.6,
                max_tokens=4000,
                usage_out=usage_out,
            )
        else:
            raise ValueError(
                f"Неизвестная модель: {model}. "
                f"Доступные: gigachat, openrouter, reasoning, openai, yandexgpt, ollama"
            )

        dt_ms = int((time.monotonic() - t0) * 1000)

        # Use real token counts if provider returned them; fall back to estimate
        tokens_in = usage_out.get("tokens_in", _estimate_tokens(user_message))
        tokens_out = usage_out.get("tokens_out", _estimate_tokens(result))
        cost_usd = _calc_cost(model, tokens_in, tokens_out)

        if telegram_id:
            try:
                from services.usage_service import log_request
                from services.limiter import increment_usage

                log_request(
                    telegram_id=telegram_id,
                    provider=model,
                    model=model,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost=cost_usd,
                    duration_ms=dt_ms,
                    success=True,
                )
                increment_usage(telegram_id, tokens_in + tokens_out)
            except Exception as log_err:
                logger.warning("usage_log_failed", extra={"error": str(log_err)})

        logger.info(
            "llm_request_finished",
            extra={
                "event": "llm_request_finished",
                "request_id": request_id,
                "user_id_hash": user_id_hash,
                "provider": model,
                "duration_ms": dt_ms,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": round(cost_usd, 6),
                "reply_len": len(result or ""),
                "success": True,
            },
        )
        return result

    except Exception as e:
        dt_ms = int((time.monotonic() - t0) * 1000)
        if telegram_id:
            try:
                from services.usage_service import log_request

                log_request(
                    telegram_id=telegram_id,
                    provider=model,
                    model=model,
                    tokens_in=_estimate_tokens(user_message),
                    tokens_out=0,
                    duration_ms=dt_ms,
                    success=False,
                    error_text=str(e)[:500],
                )
            except Exception as log_err:
                logger.warning("usage_log_failed", extra={"error": str(log_err)})
        logger.exception(
            "llm_request_failed",
            extra={
                "event": "llm_request_failed",
                "request_id": request_id,
                "user_id_hash": user_id_hash,
                "provider": model,
                "duration_ms": dt_ms,
                "success": False,
                "error_type": type(e).__name__,
            },
        )
        raise
