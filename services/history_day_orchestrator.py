"""
Bot-facing orchestration for the History Day feature.

This module glues together:
- scenario tools
- real Haystack tool invocation
- Telegram-friendly formatting
- saved-context prompt injection for follow-up questions
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
import uuid
from typing import Any

import services.persona_service as persona_svc
from services import history_day_memory_service as memory_svc
from services.history_day_haystack_adapter import CompatibleToolCall
from services.history_day_real_haystack import invoke_tool_call_via_haystack
from services.history_day_tools import (
    HISTORY_DAY_FACT_SCENARIO_TAG,
    HISTORY_DAY_IMAGE_SCENARIO_TAG,
    HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME,
    HISTORY_DAY_IMAGE_TOOL_NAME,
    HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME,
    build_fact_of_the_day_registry,
    build_related_image_registry,
    build_saved_context_messages,
    build_saved_context_registry,
    remember_fact_of_the_day_user_message,
    remember_related_image_user_message,
    remember_saved_context_user_message,
)
from telemetry import text_meta, user_id_hash
from user_storage import get_user_model
from utils import get_chat_response

logger = logging.getLogger("blabber")

TRANSLATION_SYSTEM_PROMPT = (
    "Переведи текст на русский язык. "
    "Сохраняй факты, даты, числа, имена собственные и географические названия максимально точно. "
    "Не добавляй пояснений от себя. Верни только перевод."
)


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _should_translate_to_russian(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False
    if re.search(r"[А-Яа-яЁё]", text):
        return False
    return bool(re.search(r"[A-Za-z]", text))


def _translate_to_russian(text: str, telegram_id: int) -> str:
    text = (text or "").strip()
    if not _should_translate_to_russian(text):
        return text

    model = get_user_model(telegram_id)
    request_id = uuid.uuid4().hex
    try:
        translated, _cost = get_chat_response(
            user_message=text,
            model=model,
            history=[],
            system_message=TRANSLATION_SYSTEM_PROMPT,
            request_id=request_id,
            user_id_hash=user_id_hash(telegram_id),
            telegram_id=telegram_id,
        )
        translated = (translated or "").strip()
        return translated or text
    except Exception as exc:
        logger.warning(
            "history_day_translation_failed",
            extra={
                "event": "history_day_translation_failed",
                "user_id_hash": user_id_hash(telegram_id),
                "request_id": request_id,
                "error": str(exc)[:200],
                **text_meta(text),
            },
        )
        return text


def _invoke_tool(
    *,
    registry,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    observation = invoke_tool_call_via_haystack(
        tool_call=CompatibleToolCall(
            id=uuid.uuid4().hex,
            name=tool_name,
            arguments=json.dumps(arguments, ensure_ascii=False),
        ),
        registry=registry,
    )
    return observation.get("result") or {}


def _build_source_line(title: str, url: str) -> str:
    if title and url:
        return f'🔗 Источник: <a href="{_escape(url)}">{_escape(title)}</a>'
    if url:
        return f'🔗 Источник: <a href="{_escape(url)}">{_escape(url)}</a>'
    return ""


def _build_memory_line(memory_result: dict[str, Any]) -> str:
    if not memory_result:
        return ""
    if memory_result.get("action") == "saved":
        return "🧠 Запрос сохранен в память сценария."
    if memory_result.get("fallback_reason") == "embeddings_unavailable":
        return "🧠 Память сценария сейчас недоступна: embeddings не настроены."
    if memory_result.get("fallback_reason") == "lancedb_unavailable":
        return "🧠 Память сценария временно недоступна."
    return ""


def get_history_day_status(telegram_id: int) -> dict[str, Any]:
    """Return lightweight feature status for UI/help responses."""
    saved_messages = memory_svc.list_saved_messages(telegram_id, limit=500)
    return {
        "saved_messages_count": len(saved_messages),
        "memory_available": memory_svc.is_memory_search_available(),
        "vision_available": bool(os.getenv("OPENAI_API_KEY")),
    }


def get_latest_history_day_event_date(telegram_id: int) -> str:
    """Return the most recent non-empty scenario event_date for fact/image flows."""
    rows = memory_svc.list_saved_messages(telegram_id, limit=50)
    for row in rows:
        if (row.get("scenario_tag") or "") not in {HISTORY_DAY_FACT_SCENARIO_TAG, HISTORY_DAY_IMAGE_SCENARIO_TAG}:
            continue
        event_date = str(row.get("event_date") or "").strip()
        if event_date:
            return event_date
    return ""


def get_history_day_memory_snapshot(telegram_id: int, *, limit: int = 10) -> dict[str, Any]:
    """Return a lightweight diagnostic snapshot of saved scenario memory."""
    rows = memory_svc.list_saved_messages(telegram_id, limit=limit)
    items = [
        {
            "scenario_tag": str(row.get("scenario_tag") or ""),
            "event_date": str(row.get("event_date") or ""),
            "created_at": str(row.get("created_at") or ""),
            "source_kind": str(row.get("source_kind") or ""),
            "command_name": str(row.get("command_name") or ""),
            "text": _clip(str(row.get("text") or ""), 180),
        }
        for row in rows
    ]
    snapshot = {
        "ok": True,
        "memory_available": memory_svc.is_memory_search_available(),
        "latest_event_date": get_latest_history_day_event_date(telegram_id),
        "saved_messages_count": len(memory_svc.list_saved_messages(telegram_id, limit=500)),
        "items": items,
    }
    logger.info(
        "history_day_memory_snapshot_built",
        extra={
            "event": "history_day_memory_snapshot_built",
            "user_id_hash": user_id_hash(telegram_id),
            "items_count": len(items),
            "latest_event_date": snapshot["latest_event_date"],
        },
    )
    return snapshot


def run_fact_scenario(
    telegram_id: int,
    *,
    user_message: str,
    date: str = "",
) -> dict[str, Any]:
    """Run Scenario 1 via real Haystack tool invocation."""
    logger.info(
        "history_day_fact_started",
        extra={
            "event": "history_day_fact_started",
            "user_id_hash": user_id_hash(telegram_id),
            "date": date,
            **text_meta(user_message),
        },
    )
    memory_result = remember_fact_of_the_day_user_message(
        telegram_id,
        user_message=user_message,
        date=date,
    )
    registry = build_fact_of_the_day_registry()
    result = _invoke_tool(
        registry=registry,
        tool_name="history_fact_of_the_day",
        arguments={"date": date, "language": "en"},
    )
    if not result.get("ok"):
        logger.info(
            "history_day_fact_failed",
            extra={
                "event": "history_day_fact_failed",
                "user_id_hash": user_id_hash(telegram_id),
                "date": date,
                "reason": result.get("error") or result.get("message") or "unknown",
            },
        )
        return {
            "ok": False,
            "text": (
                "📅 <b>История дня</b>\n\n"
                "Не удалось получить исторический факт из внешнего источника.\n"
                f"Причина: {_escape(result.get('message') or result.get('error') or 'неизвестная ошибка')}"
            ),
        }

    translated_event = _translate_to_russian(str(result.get("event", "")), telegram_id)
    lines = [
        f"📅 <b>История дня · {result.get('date', '')}</b>",
        "",
        f"<b>{_escape(result.get('year'))}</b> — {_escape(translated_event)}",
    ]
    source_line = _build_source_line(str(result.get("source_title") or ""), str(result.get("source_url") or ""))
    if source_line:
        lines.extend(["", source_line])
    if result.get("fallback_used"):
        lines.extend(["", "ℹ️ Использован резервный путь получения факта."])
    memory_line = _build_memory_line(memory_result)
    if memory_line:
        lines.extend(["", memory_line])
    logger.info(
        "history_day_fact_completed",
        extra={
            "event": "history_day_fact_completed",
            "user_id_hash": user_id_hash(telegram_id),
            "date": result.get("date", ""),
            "year": result.get("year"),
            "fallback_used": bool(result.get("fallback_used")),
        },
    )

    return {
        "ok": True,
        "text": "\n".join(lines).strip(),
        "source_url": result.get("source_url", ""),
        "memory_result": memory_result,
        "result": result,
    }


def run_image_scenario(
    telegram_id: int,
    *,
    user_message: str,
    date: str = "",
    image_question: str = "",
) -> dict[str, Any]:
    """Run Scenario 2 via real Haystack tool invocation."""
    logger.info(
        "history_day_image_started",
        extra={
            "event": "history_day_image_started",
            "user_id_hash": user_id_hash(telegram_id),
            "date": date,
            "has_image_question": bool((image_question or "").strip()),
            **text_meta(user_message),
        },
    )
    memory_result = remember_related_image_user_message(
        telegram_id,
        user_message=user_message,
        date=date,
    )
    registry = build_related_image_registry()
    image_result = _invoke_tool(
        registry=registry,
        tool_name=HISTORY_DAY_IMAGE_TOOL_NAME,
        arguments={"date": date, "language": "en"},
    )
    if not image_result.get("ok"):
        logger.info(
            "history_day_image_failed",
            extra={
                "event": "history_day_image_failed",
                "user_id_hash": user_id_hash(telegram_id),
                "date": date,
                "reason": image_result.get("error") or image_result.get("message") or "unknown",
            },
        )
        return {
            "ok": False,
            "text": (
                "🖼 <b>История дня · изображение</b>\n\n"
                f"{_escape(image_result.get('message') or image_result.get('error') or 'Не удалось подобрать изображение.')}"
            ),
            "memory_result": memory_result,
        }

    analysis_result = _invoke_tool(
        registry=registry,
        tool_name=HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME,
        arguments={
            "image_url": image_result.get("image_url", ""),
            "event": image_result.get("event", ""),
            "year": image_result.get("year"),
            "page_title": image_result.get("page_title", ""),
            "page_description": image_result.get("page_description", ""),
            "question": image_question,
        },
    )

    translated_event = _translate_to_russian(str(image_result.get("event", "")), telegram_id)
    caption_bits = [
        f"🖼 История дня · {image_result.get('date', '')}",
        f"{image_result.get('year')} — {_clip(translated_event, 180)}",
    ]
    photo_caption = "\n".join(bit for bit in caption_bits if bit).strip()

    lines = [
        "🖼 <b>Связанное изображение</b>",
        "",
        f"<b>{_escape(image_result.get('year'))}</b> — {_escape(translated_event)}",
    ]
    if image_question:
        lines.append(f"Вопрос: <i>{_escape(image_question)}</i>")
    if image_result.get("page_title"):
        lines.append(f"Связанная страница: <b>{_escape(image_result.get('page_title'))}</b>")
    source_line = _build_source_line(str(image_result.get("source_title") or ""), str(image_result.get("source_url") or ""))
    if source_line:
        lines.extend(["", source_line])
    if analysis_result.get("analysis_text"):
        lines.extend(["", f"🔎 <b>Анализ</b>\n{_escape(analysis_result.get('analysis_text', ''))}"])
    if analysis_result.get("fallback_used"):
        lines.extend(["", "ℹ️ Vision недоступен, поэтому использовано описание по метаданным."])
    memory_line = _build_memory_line(memory_result)
    if memory_line:
        lines.extend(["", memory_line])
    logger.info(
        "history_day_image_completed",
        extra={
            "event": "history_day_image_completed",
            "user_id_hash": user_id_hash(telegram_id),
            "date": image_result.get("date", ""),
            "year": image_result.get("year"),
            "analysis_mode": analysis_result.get("analysis_mode", ""),
            "analysis_fallback_used": bool(analysis_result.get("fallback_used")),
        },
    )

    return {
        "ok": True,
        "image_url": image_result.get("image_url", ""),
        "photo_caption": _clip(photo_caption, 900),
        "text": "\n".join(lines).strip(),
        "source_url": image_result.get("source_url", ""),
        "memory_result": memory_result,
        "image_result": image_result,
        "analysis_result": analysis_result,
    }


def _build_context_fallback_answer(
    *,
    question: str,
    retrieval: dict[str, Any],
) -> str:
    if retrieval.get("fallback_reason") == "embeddings_unavailable":
        return (
            "🧠 <b>Память сценария</b>\n\n"
            "Сейчас не могу выполнить семантический поиск: embeddings недоступны.\n"
            "Поэтому честно не буду делать вид, что что-то вспомнил."
        )
    if retrieval.get("fallback_reason") == "no_saved_messages":
        return (
            "🧠 <b>Память сценария</b>\n\n"
            "Пока у меня нет сохраненных пользовательских сообщений по `Истории дня`.\n"
            "Сначала попроси факт дня или изображение, а потом задай уточняющий вопрос."
        )
    if retrieval.get("fallback_reason") == "no_matches":
        return (
            "🧠 <b>Память сценария</b>\n\n"
            "Я посмотрел в сохраненный контекст, но не нашел достаточно релевантных записей под этот вопрос.\n"
            f"Вопрос: <i>{_escape(question)}</i>"
        )
    return (
        "🧠 <b>Память сценария</b>\n\n"
        "Пока не удалось собрать ответ по сохраненному контексту."
    )


def _infer_context_question_kind(question: str) -> str:
    lowered = (question or "").strip().lower()
    if "в какой стране" in lowered or "какая страна" in lowered or "стране" in lowered:
        return "country"
    if "где" in lowered or "в каком месте" in lowered or "в каком городе" in lowered:
        return "location"
    if "год" in lowered:
        return "year"
    if "фигур" in lowered:
        return "figure_or_event"
    if "событ" in lowered:
        return "event"
    if "о чем" in lowered or "рассказывал" in lowered:
        return "summary"
    return "generic"


def _extract_country_from_fact(fact_result: dict[str, Any]) -> str:
    event = str(fact_result.get("event") or "").strip().rstrip(".")
    if not event:
        return ""

    # Common Wikimedia phrasing: "... in City, Country"
    if ", " in event:
        tail = event.rsplit(", ", 1)[-1].strip()
        if tail and len(tail.split()) <= 4:
            return tail

    lowered = event.lower()
    marker = " in "
    if marker in lowered:
        idx = lowered.rfind(marker)
        tail = event[idx + len(marker):].strip()
        if ", " in tail:
            country = tail.rsplit(", ", 1)[-1].strip()
            if country:
                return country
    return ""


def _extract_location_from_fact(fact_result: dict[str, Any]) -> str:
    event = str(fact_result.get("event") or "").strip().rstrip(".")
    if not event:
        return ""

    lowered = event.lower()
    marker = " in "
    if marker in lowered:
        idx = lowered.rfind(marker)
        return event[idx + len(marker):].strip()
    return ""


def _build_structured_context_answer(
    *,
    question: str,
    retrieval: dict[str, Any],
    telegram_id: int,
) -> str | None:
    items = retrieval.get("items") or []
    if not items:
        return None

    top_item = next((item for item in items if item.get("event_date")), items[0])
    event_date = str(top_item.get("event_date") or "").strip()
    if not event_date:
        return None

    fact_registry = build_fact_of_the_day_registry()
    fact_result = _invoke_tool(
        registry=fact_registry,
        tool_name="history_fact_of_the_day",
        arguments={"date": event_date, "language": "en"},
    )
    if not fact_result.get("ok"):
        return None

    kind = _infer_context_question_kind(question)
    year = _escape(fact_result.get("year"))
    translated_event = _translate_to_russian(str(fact_result.get("event", "")), telegram_id)
    event = _escape(translated_event)
    page_title = _escape(fact_result.get("page_title") or fact_result.get("source_title") or "")
    lines = ["🧠 <b>По сохраненному контексту</b>", ""]

    if kind == "country":
        country = _escape(_extract_country_from_fact(fact_result))
        if country:
            lines.append(f"Это было в <b>{country}</b>.")
        else:
            lines.append("Я поднял событие из памяти, но не смог надежно извлечь страну из доступного факта.")
        lines.append(f"Событие: <b>{year}</b> — {event}")
    elif kind == "location":
        location = _escape(_extract_location_from_fact(fact_result))
        if location:
            lines.append(f"Это произошло в <b>{location}</b>.")
        else:
            lines.append("Я поднял событие из памяти, но не смог надежно извлечь место из доступного факта.")
        lines.append(f"Событие: <b>{year}</b> — {event}")
    elif kind == "year":
        lines.append(f"Это связано с <b>{year}</b> годом.")
        if event:
            lines.append(f"Событие: {event}")
    elif kind in {"summary", "event", "generic"}:
        lines.append(f"Я рассказывал про событие от <b>{_escape(event_date)}</b>:")
        lines.append(f"<b>{year}</b> — {event}")
    elif kind == "figure_or_event":
        if page_title:
            lines.append(f"Ключевая связанная сущность: <b>{page_title}</b>.")
        lines.append(f"Событие: <b>{year}</b> — {event}")

    source_line = _build_source_line(
        str(fact_result.get("source_title") or fact_result.get("page_title") or ""),
        str(fact_result.get("source_url") or fact_result.get("page_url") or ""),
    )
    if source_line:
        lines.extend(["", source_line])
    return "\n".join(lines).strip()


def run_saved_context_scenario(
    telegram_id: int,
    *,
    user_message: str,
) -> dict[str, Any]:
    """Run Scenario 3: retrieval from saved LanceDB context plus prompt injection."""
    logger.info(
        "history_day_context_started",
        extra={
            "event": "history_day_context_started",
            "user_id_hash": user_id_hash(telegram_id),
            **text_meta(user_message),
        },
    )
    prompt_payload = build_saved_context_messages(
        telegram_id,
        user_message=user_message,
    )
    retrieval = prompt_payload["retrieval"]
    if retrieval.get("found_count", 0) <= 0:
        remember_saved_context_user_message(telegram_id, user_message=user_message)
        logger.info(
            "history_day_context_empty",
            extra={
                "event": "history_day_context_empty",
                "user_id_hash": user_id_hash(telegram_id),
                "fallback_reason": retrieval.get("fallback_reason"),
            },
        )
        return {
            "ok": True,
            "text": _build_context_fallback_answer(question=user_message, retrieval=retrieval),
            "retrieval": retrieval,
        }

    registry = build_saved_context_registry(telegram_id)
    lookup_result = _invoke_tool(
        registry=registry,
        tool_name=HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME,
        arguments={"query": user_message, "top_k": 3},
    )

    structured_answer = _build_structured_context_answer(
        question=user_message,
        retrieval=lookup_result or retrieval,
        telegram_id=telegram_id,
    )
    if structured_answer:
        remember_saved_context_user_message(telegram_id, user_message=user_message)
        logger.info(
            "history_day_context_completed",
            extra={
                "event": "history_day_context_completed",
                "user_id_hash": user_id_hash(telegram_id),
                "found_count": lookup_result.get("found_count", retrieval.get("found_count", 0)),
                "mode": "structured",
            },
        )
        footer_lines = [
            "",
            "🧠 <b>Сохраненный контекст</b>: найдено "
            f"{lookup_result.get('found_count', retrieval.get('found_count', 0))} записей в LanceDB.",
        ]
        return {
            "ok": True,
            "text": (structured_answer + "\n" + "\n".join(footer_lines)).strip(),
            "retrieval": lookup_result or retrieval,
        }

    messages = prompt_payload["messages"]
    system_message = str(messages[0]["content"])
    persona_addon = persona_svc.build_persona_addon(telegram_id)
    if persona_addon:
        system_message += f"\n\nРоль для ответа:\n{persona_addon}"

    model = get_user_model(telegram_id)
    request_id = uuid.uuid4().hex
    try:
        answer, _cost = get_chat_response(
            user_message=messages[1]["content"],
            model=model,
            history=[],
            system_message=system_message,
            request_id=request_id,
            user_id_hash=user_id_hash(telegram_id),
            telegram_id=telegram_id,
        )
        answer = _escape((answer or "").strip())
    except Exception as exc:
        logger.warning(
            "history_day_context_llm_failed",
            extra={
                "event": "history_day_context_llm_failed",
                "user_id_hash": user_id_hash(telegram_id),
                "request_id": request_id,
                "error": str(exc)[:200],
                **text_meta(user_message),
            },
        )
        top_item = (lookup_result.get("items") or retrieval.get("items") or [{}])[0]
        answer = (
            "🧠 Я поднял сохраненный контекст из LanceDB.\n\n"
            f"Похоже, речь шла вот об этом: {_escape(top_item.get('text') or 'контекст найден, но краткое резюме не собрано')}"
        )

    remember_saved_context_user_message(telegram_id, user_message=user_message)
    logger.info(
        "history_day_context_completed",
        extra={
            "event": "history_day_context_completed",
            "user_id_hash": user_id_hash(telegram_id),
            "found_count": lookup_result.get("found_count", retrieval.get("found_count", 0)),
            "mode": "llm",
        },
    )

    footer_lines = [
        "",
        "🧠 <b>Сохраненный контекст</b>: найдено "
        f"{lookup_result.get('found_count', retrieval.get('found_count', 0))} записей в LanceDB.",
    ]
    return {
        "ok": True,
        "text": (answer + "\n" + "\n".join(footer_lines)).strip(),
        "retrieval": lookup_result or retrieval,
    }


def clear_history_day_memory(telegram_id: int) -> dict[str, Any]:
    """Clear all saved scenario memory for the feature."""
    ok = memory_svc.clear_user_memory(telegram_id)
    return {
        "ok": ok,
        "text": (
            "🧹 Память сценария `История дня` очищена."
            if ok
            else "Не получилось очистить память сценария `История дня`."
        ),
    }
