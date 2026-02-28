"""
Модуль озвучки текста (Text-to-Speech) через Yandex SpeechKit.

Использует REST API v1 Yandex Cloud SpeechKit. Генерирует OGG Opus
напрямую — без ffmpeg. Требуется YANDEX_API_KEY и YANDEX_FOLDER_ID
(те же, что для Yandex GPT; нужна роль speechkit.speaker у сервисного аккаунта).

Использование:
    from tts import synthesize_voice

    ogg_bytes = synthesize_voice("Привет, мир!")
    # -> bytes (OGG Opus), готовые для bot.send_voice(chat_id, ogg_bytes)
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

import requests

from services.config_registry import get_setting

logger = logging.getLogger("blabber")

# API v1 endpoint (до 5000 символов, OGG Opus)
TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

# Доступные голоса (v1): jane, oksana (legacy), alena, filipp, ermil, zahar, omazh, marina...
# Полный список: https://cloud.yandex.ru/docs/speechkit/tts/voices
VOICES = {
    "alena": "alena",      # Женский, neutral/good
    "filipp": "filipp",    # Мужской
    "ermil": "ermil",      # Мужской, neutral/good
    "jane": "jane",        # Женский, neutral/good/evil
    "omazh": "omazh",      # Женский, neutral/evil
    "zahar": "zahar",      # Мужской, neutral/good
    "marina": "marina",    # Женский (default в SpeechKit)
}

DEFAULT_VOICE = "alena"

# Эмоция для «балабола» — good (бодрый, дружелюбный)
DEFAULT_EMOTION = "good"


def _get_tts_max_chars() -> int:
    """Max characters for TTS (from config or env)."""
    val = get_setting("tts_max_chars", 5000, env_key="TTS_MAX_CHARS")
    try:
        return int(val) if val is not None else 5000
    except (ValueError, TypeError):
        return 5000


def _strip_markdown(text: str) -> str:
    """Убрать markdown-разметку."""
    text = re.sub(r"```[\s\S]*?```", " фрагмент кода ", text)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def _truncate_for_tts(text: str, max_chars: int | None = None) -> str:
    """Обрезать текст до max_chars по границе предложения."""
    if max_chars is None:
        max_chars = _get_tts_max_chars()
    if len(text) <= max_chars:
        return text
    cut = text.rfind(". ", 0, max_chars)
    if cut < max_chars // 2:
        cut = text.rfind("! ", 0, max_chars)
    if cut < max_chars // 2:
        cut = text.rfind("? ", 0, max_chars)
    if cut < max_chars // 2:
        cut = text.rfind("\n", 0, max_chars)
    if cut < max_chars // 2:
        cut = max_chars
    return text[: cut + 1].rstrip()


def _synthesize_yandex(
    text: str,
    voice: str,
    emotion: str,
    api_key: str,
    folder_id: str,
) -> bytes:
    """Синтез речи через Yandex SpeechKit REST API v1."""
    # Не все голоса поддерживают emotion; для filipp emotion не нужен
    data = {
        "text": text,
        "lang": "ru-RU",
        "voice": voice,
        "folderId": folder_id,
        "format": "oggopus",
    }
    if voice not in ("filipp",):
        data["emotion"] = emotion

    headers = {"Authorization": f"Api-Key {api_key}"}

    resp = requests.post(
        TTS_URL,
        headers=headers,
        data=data,
        timeout=30,
        stream=True,
    )

    if resp.status_code != 200:
        err_text = resp.text[:500] if resp.text else ""
        raise RuntimeError(
            f"Yandex SpeechKit TTS error: HTTP {resp.status_code}. {err_text}"
        )

    return resp.content


def synthesize_voice(
    text: str,
    voice_key: Optional[str] = None,
) -> bytes:
    """
    Синтезировать голосовое сообщение из текста через Yandex SpeechKit.

    Args:
        text: Текст для озвучки (может содержать markdown).
        voice_key: Ключ голоса (alena, filipp, ermil, jane, omazh, zahar, marina).

    Returns:
        bytes — OGG Opus аудио для bot.send_voice().
    """
    if not text or not text.strip():
        raise ValueError("Текст для озвучки пустой")

    voice_key = voice_key or DEFAULT_VOICE
    voice = VOICES.get(voice_key)
    if not voice:
        raise ValueError(
            f"Неизвестный голос: '{voice_key}'. "
            f"Доступные: {', '.join(VOICES.keys())}"
        )

    api_key = os.getenv("YANDEX_API_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    if not api_key or not folder_id:
        raise ValueError(
            "Для озвучки нужны YANDEX_API_KEY и YANDEX_FOLDER_ID в .env. "
            "Используются те же ключи, что для Yandex GPT. "
            "У сервисного аккаунта должна быть роль speechkit.speaker."
        )

    clean = _strip_markdown(text)
    clean = _truncate_for_tts(clean)
    if not clean.strip():
        raise ValueError("После очистки текст для озвучки пустой")

    logger.info(
        "tts_started",
        extra={"event": "tts_started", "voice": voice_key, "text_len": len(clean)},
    )

    ogg_data = _synthesize_yandex(
        text=clean,
        voice=voice,
        emotion=DEFAULT_EMOTION,
        api_key=api_key,
        folder_id=folder_id,
    )

    if not ogg_data:
        raise RuntimeError("Yandex SpeechKit вернул пустой ответ")

    logger.info(
        "tts_finished",
        extra={
            "event": "tts_finished",
            "voice": voice_key,
            "text_len": len(clean),
            "ogg_size": len(ogg_data),
        },
    )

    return ogg_data


def get_available_voices() -> dict[str, str]:
    """Словарь доступных голосов {key: description}."""
    return {
        "alena": "Алёна (женский)",
        "filipp": "Филипп (мужской)",
        "ermil": "Ермил (мужской)",
        "jane": "Джейн (женский)",
        "omazh": "Омаж (женский)",
        "zahar": "Захар (мужской)",
        "marina": "Марина (женский)",
    }
