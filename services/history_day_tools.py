"""
Scenario tools and prompt helpers for the History Day feature.
"""

from __future__ import annotations

from typing import Any

from services import history_day_context_service as context_svc
from services import history_day_fact_service as fact_svc
from services import history_day_image_service as image_svc
from services import history_day_memory_service as memory_svc
from services.history_day_haystack_adapter import (
    HaystackCompatibleTool,
    HaystackCompatibleToolRegistry,
    build_agent_messages,
)

HISTORY_DAY_FACT_SCENARIO_TAG = "history_day_fact"
HISTORY_DAY_IMAGE_SCENARIO_TAG = "history_day_image"
HISTORY_DAY_CONTEXT_SCENARIO_TAG = "history_day_context"
HISTORY_DAY_FACT_TOOL_NAME = "history_fact_of_the_day"
HISTORY_DAY_IMAGE_TOOL_NAME = "history_related_image"
HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME = "history_image_analysis"
HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME = "history_saved_context_lookup"

HISTORY_DAY_FACT_SYSTEM_PROMPT = (
    "Ты ведешь сценарий `История дня`. "
    "Когда пользователь спрашивает, что произошло сегодня в истории, просит факт дня, "
    "спрашивает про конкретную дату или хочет короткий исторический факт по дню, "
    f"используй инструмент `{HISTORY_DAY_FACT_TOOL_NAME}`. "
    "На текущем этапе используй только общую историю, без узкой тематической фильтрации. "
    "Сначала опирайся на данные инструмента, затем кратко и ясно объясняй результат. "
    "Если инструмент вернул ошибку или пустой результат, честно скажи, что внешний источник сейчас недоступен, "
    "и не выдумывай факты."
)

HISTORY_DAY_IMAGE_SYSTEM_PROMPT = (
    "Ты ведешь сценарий `История дня`, этап изображения и анализа. "
    f"Если пользователь просит показать изображение по факту дня, используй `{HISTORY_DAY_IMAGE_TOOL_NAME}`. "
    f"Если нужно описать или проанализировать найденное изображение, используй `{HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME}`. "
    "Сначала получай изображение и его метаданные, затем отдельно анализируй изображение. "
    "Возвращай результат в понятном виде: краткая подводка, изображение/ссылка на него, потом анализ. "
    "Если изображение не найдено или vision недоступен, говори об этом честно и используй fallback-описание без выдумок."
)

HISTORY_DAY_CONTEXT_SYSTEM_PROMPT = (
    "Ты ведешь сценарий `История дня`, этап ответа по сохраненному контексту. "
    f"Для уточняющих вопросов используй инструмент `{HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME}` "
    "или injected saved context, если он уже передан в system prompt. "
    "Типовые вопросы этого сценария: "
    + "; ".join(f"«{question}»" for question in context_svc.MEMORY_DEMO_QUESTIONS)
    + ". "
    "Если найденный контекст помогает, опирайся на него явно. "
    "Если retrieval ничего не нашел, честно скажи, что в сохраненной памяти недостаточно данных. "
    "Не подменяй saved context обычной KB и не делай вид, будто что-то помнишь без retrieval."
)


def build_fact_of_the_day_tool() -> HaystackCompatibleTool:
    """Create the compatible tool definition for Sprint 4."""
    return HaystackCompatibleTool(
        name=HISTORY_DAY_FACT_TOOL_NAME,
        description=(
            "Возвращает реальный исторический факт дня по указанной дате или по сегодняшнему дню. "
            "Используй для запросов вида: что произошло сегодня в истории, факт дня, событие по дате."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Необязательная дата в формате MM-DD, MM/DD или YYYY-MM-DD.",
                },
                "language": {
                    "type": "string",
                    "description": "Язык Wikipedia API, по умолчанию en.",
                    "default": "en",
                },
            },
        },
        handler=fact_svc.get_fact_of_the_day,
    )


def build_fact_of_the_day_registry() -> HaystackCompatibleToolRegistry:
    """Create a registry containing the Scenario 1 tool set."""
    registry = HaystackCompatibleToolRegistry()
    registry.register(build_fact_of_the_day_tool())
    return registry


def build_related_image_tool() -> HaystackCompatibleTool:
    """Create the related image tool for Sprint 5."""
    return HaystackCompatibleTool(
        name=HISTORY_DAY_IMAGE_TOOL_NAME,
        description=(
            "Возвращает связанное изображение по историческому факту дня вместе с метаданными. "
            "Используй, когда нужно показать картинку по событию дня или найти иллюстрацию к факту."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Необязательная дата в формате MM-DD, MM/DD или YYYY-MM-DD.",
                },
                "language": {
                    "type": "string",
                    "description": "Язык Wikipedia API, по умолчанию en.",
                    "default": "en",
                },
            },
        },
        handler=image_svc.get_related_image_for_fact,
    )


def build_image_analysis_tool() -> HaystackCompatibleTool:
    """Create the image analysis tool for Sprint 5."""
    return HaystackCompatibleTool(
        name=HISTORY_DAY_IMAGE_ANALYSIS_TOOL_NAME,
        description=(
            "Анализирует историческое изображение по URL и кратко объясняет, что на нем видно "
            "и как оно связано с фактом дня."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "image_url": {"type": "string", "description": "URL изображения для анализа."},
                "event": {"type": "string", "description": "Текст исторического события."},
                "year": {"type": "integer", "description": "Год события."},
                "page_title": {"type": "string", "description": "Название связанной страницы Wikimedia."},
                "page_description": {"type": "string", "description": "Краткое описание страницы Wikimedia."},
                "question": {"type": "string", "description": "Необязательный конкретный вопрос пользователя про изображение."},
            },
            "required": ["image_url"],
        },
        handler=image_svc.analyze_related_image,
    )


def build_related_image_registry() -> HaystackCompatibleToolRegistry:
    """Create a registry containing the Scenario 2 tool set."""
    registry = HaystackCompatibleToolRegistry()
    registry.register_many(
        [
            build_fact_of_the_day_tool(),
            build_related_image_tool(),
            build_image_analysis_tool(),
        ]
    )
    return registry


def build_saved_context_lookup_tool(telegram_id: int) -> HaystackCompatibleTool:
    """Create a user-scoped saved-context lookup tool for Sprint 6."""

    def _lookup_saved_context(query: str, top_k: int = context_svc.DEFAULT_CONTEXT_TOP_K) -> dict[str, Any]:
        return context_svc.retrieve_saved_context(
            telegram_id,
            query=query,
            top_k=top_k,
        )

    return HaystackCompatibleTool(
        name=HISTORY_DAY_SAVED_CONTEXT_TOOL_NAME,
        description=(
            "Ищет в сохраненной LanceDB-памяти пользователя контекст по уточняющему вопросу. "
            "Используй для вопросов вида: о чем ты только что рассказывал, с каким годом это связано, "
            "напомни событие или ключевую фигуру."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Уточняющий вопрос пользователя."},
                "top_k": {
                    "type": "integer",
                    "description": "Сколько наиболее релевантных фрагментов искать.",
                    "default": context_svc.DEFAULT_CONTEXT_TOP_K,
                },
            },
            "required": ["query"],
        },
        handler=_lookup_saved_context,
    )


def build_saved_context_registry(telegram_id: int) -> HaystackCompatibleToolRegistry:
    """Create a registry containing the Scenario 3 tool set."""
    registry = HaystackCompatibleToolRegistry()
    registry.register(build_saved_context_lookup_tool(telegram_id))
    return registry


def build_fact_of_the_day_messages(
    *,
    user_message: str,
    context_blocks: list[str] | None = None,
) -> list[dict[str, str]]:
    """Build prompt messages for the Scenario 1 flow."""
    return build_agent_messages(
        system_prompt=HISTORY_DAY_FACT_SYSTEM_PROMPT,
        user_message=user_message,
        context_blocks=context_blocks,
    )


def build_related_image_messages(
    *,
    user_message: str,
    context_blocks: list[str] | None = None,
) -> list[dict[str, str]]:
    """Build prompt messages for the Scenario 2 flow."""
    return build_agent_messages(
        system_prompt=HISTORY_DAY_IMAGE_SYSTEM_PROMPT,
        user_message=user_message,
        context_blocks=context_blocks,
    )


def build_saved_context_messages(
    telegram_id: int,
    *,
    user_message: str,
    top_k: int = context_svc.DEFAULT_CONTEXT_TOP_K,
) -> dict[str, Any]:
    """
    Build prompt messages for Scenario 3 and inject retrieved LanceDB context.

    Returns both the messages and the retrieval payload for observability/tests.
    """
    retrieval = context_svc.retrieve_saved_context(
        telegram_id,
        query=user_message,
        top_k=top_k,
    )
    context_blocks = [retrieval["context_block"]] if retrieval.get("context_block") else []
    messages = build_agent_messages(
        system_prompt=HISTORY_DAY_CONTEXT_SYSTEM_PROMPT,
        user_message=user_message,
        context_blocks=context_blocks,
    )
    return {
        "messages": messages,
        "retrieval": retrieval,
    }


def remember_fact_of_the_day_user_message(
    telegram_id: int,
    *,
    user_message: str,
    date: str = "",
) -> dict[str, Any]:
    """Persist the user request in scenario memory before/after tool processing."""
    normalized_date = fact_svc.normalize_requested_date(date)
    event_date = normalized_date["date"] if normalized_date.get("ok") else ""
    return memory_svc.save_user_message(
        telegram_id,
        role="user",
        text=user_message,
        scenario_tag=HISTORY_DAY_FACT_SCENARIO_TAG,
        command_name="history_day_fact",
        event_date=event_date,
    )


def remember_related_image_user_message(
    telegram_id: int,
    *,
    user_message: str,
    date: str = "",
) -> dict[str, Any]:
    """Persist the user request for the related image scenario."""
    normalized_date = fact_svc.normalize_requested_date(date)
    event_date = normalized_date["date"] if normalized_date.get("ok") else ""
    return memory_svc.save_user_message(
        telegram_id,
        role="user",
        text=user_message,
        scenario_tag=HISTORY_DAY_IMAGE_SCENARIO_TAG,
        command_name="history_day_image",
        event_date=event_date,
    )


def remember_saved_context_user_message(
    telegram_id: int,
    *,
    user_message: str,
) -> dict[str, Any]:
    """Persist the user request for the saved-context scenario."""
    return memory_svc.save_user_message(
        telegram_id,
        role="user",
        text=user_message,
        scenario_tag=HISTORY_DAY_CONTEXT_SCENARIO_TAG,
        command_name="history_day_context",
        source_kind="user_clarification",
        event_date="",
    )
