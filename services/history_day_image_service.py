"""
Related image retrieval and analysis for the History Day scenario.

Strategy frozen for Sprint 5:
- image source: Wikimedia page metadata already returned by the fact service
- analyzed subject: the primary page/object/person associated with the selected fact
- flow: one tool returns image + fact metadata, another tool analyzes the image
"""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from services import history_day_fact_service as fact_svc

DEFAULT_VISION_MODEL = "gpt-4o-mini"

VISION_SYSTEM_PROMPT = (
    "Ты анализируешь историческое изображение. "
    "Опиши, что на нём видно, как это связано с историческим фактом, "
    "и какие детали пользователь должен заметить. "
    "Не выдумывай точные визуальные детали, если они неочевидны. "
    "Если уверенность низкая, скажи об этом прямо. "
    "Ответ дай кратко, в 3-5 предложениях, на русском языке."
)


def get_related_image_for_fact(date: str = "", language: str = "en") -> dict[str, Any]:
    """Return an image related to the fact of the day plus normalized metadata."""
    fact = fact_svc.get_fact_of_the_day(date=date, language=language)
    if not fact.get("ok"):
        return {
            "ok": False,
            "date": fact.get("date", date),
            "language": language,
            "error": "fact_lookup_failed",
            "message": "Не удалось получить базовый исторический факт для подбора изображения",
            "fact_result": fact,
            "fallback_used": fact.get("fallback_used", False),
            "fallback_reason": fact.get("error"),
        }

    image_url = str(fact.get("image_url") or "").strip()
    thumbnail_url = str(fact.get("thumbnail_url") or "").strip()
    final_image_url = image_url or thumbnail_url

    if not final_image_url:
        return {
            "ok": False,
            "date": fact.get("date", date),
            "language": language,
            "error": "image_not_found",
            "message": "Для этого исторического факта подходящее изображение не найдено",
            "event": fact.get("event", ""),
            "year": fact.get("year"),
            "page_title": fact.get("page_title", ""),
            "page_url": fact.get("page_url", ""),
            "fallback_used": True,
            "fallback_reason": "wikimedia_page_has_no_image",
        }

    return {
        "ok": True,
        "date": fact.get("date", date),
        "language": language,
        "year": fact.get("year"),
        "event": fact.get("event", ""),
        "page_title": fact.get("page_title", ""),
        "page_url": fact.get("page_url", ""),
        "page_description": fact.get("page_description", ""),
        "image_url": final_image_url,
        "thumbnail_url": thumbnail_url,
        "source_url": fact.get("source_url", ""),
        "source_title": fact.get("source_title", ""),
        "image_origin": "wikimedia_page_image" if image_url else "wikimedia_thumbnail",
        "fallback_used": bool(fact.get("fallback_used")),
        "fallback_reason": fact.get("fallback_reason"),
    }


def _build_metadata_fallback_analysis(
    *,
    event: str,
    year: Any,
    page_title: str,
    page_description: str,
) -> str:
    parts = []
    if page_title:
        parts.append(f"Изображение связано со страницей «{page_title}».")
    if page_description:
        parts.append(f"По метаданным Wikimedia это: {page_description}.")
    if year or event:
        event_bits = []
        if year:
            event_bits.append(str(year))
        if event:
            event_bits.append(str(event))
        parts.append("Связь с фактом дня: " + " — ".join(event_bits) + ".")
    parts.append("Полный vision-анализ сейчас недоступен, поэтому это честное описание только по доступным метаданным.")
    return " ".join(parts).strip()


def _get_vision_client() -> tuple[OpenAI | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, None
    model = os.getenv("OPENAI_VISION_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_VISION_MODEL
    return OpenAI(api_key=api_key), model


def analyze_related_image(
    *,
    image_url: str,
    event: str = "",
    year: int | None = None,
    page_title: str = "",
    page_description: str = "",
    question: str = "",
) -> dict[str, Any]:
    """Analyze one related historical image using vision or metadata fallback."""
    image_url = (image_url or "").strip()
    if not image_url:
        return {
            "ok": False,
            "error": "empty_image_url",
            "message": "Для анализа изображения нужен непустой URL",
            "fallback_used": False,
            "fallback_reason": None,
        }

    client, model = _get_vision_client()
    if client is None or model is None:
        return {
            "ok": True,
            "analysis_text": _build_metadata_fallback_analysis(
                event=event,
                year=year,
                page_title=page_title,
                page_description=page_description,
            ),
            "analysis_mode": "metadata_fallback",
            "image_url": image_url,
            "fallback_used": True,
            "fallback_reason": "vision_unavailable",
        }

    user_text = (
        "Проанализируй историческое изображение.\n"
        f"Исторический факт: {event or 'не указан'}\n"
        f"Год: {year if year is not None else 'не указан'}\n"
        f"Страница: {page_title or 'не указана'}\n"
        f"Описание страницы: {page_description or 'не указано'}"
    )
    if (question or "").strip():
        user_text += f"\nВопрос пользователя про изображение: {question.strip()}"
    try:
        completion = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=400,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        )
        analysis_text = (completion.choices[0].message.content or "").strip()
        if not analysis_text:
            raise ValueError("Empty vision response")
        return {
            "ok": True,
            "analysis_text": analysis_text,
            "analysis_mode": "vision",
            "image_url": image_url,
            "model": model,
            "fallback_used": False,
            "fallback_reason": None,
        }
    except Exception as exc:
        return {
            "ok": True,
            "analysis_text": _build_metadata_fallback_analysis(
                event=event,
                year=year,
                page_title=page_title,
                page_description=page_description,
            ),
            "analysis_mode": "metadata_fallback",
            "image_url": image_url,
            "fallback_used": True,
            "fallback_reason": f"vision_failed:{str(exc)[:120]}",
        }
