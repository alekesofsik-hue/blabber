"""
Report service — generates a PDF conversation report from chat history.

Pipeline:
  1. Get conversation history from context_service.
  2. Send it to LLM and get structured JSON summary.
  3. Render HTML template (Jinja2) with the JSON data.
  4. Convert HTML → PDF (WeasyPrint) and save to reports/.

Usage:
    from services.report_service import generate_report
    pdf_path = generate_report(telegram_id)
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import services.context_service as ctx_svc
from user_storage import get_user_model
from utils import get_chat_response

logger = logging.getLogger("blabber")

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

REPORT_SYSTEM_PROMPT = """
Ты — аналитик разговоров. Твоя задача: проанализировать диалог пользователя с ИИ-ассистентом 
и вернуть ТОЛЬКО валидный JSON-объект (без markdown-блоков, без лишнего текста).

Структура JSON строго такая:
{
  "topic": "<основная тема разговора, 1-2 предложения>",
  "key_points": ["<ключевой тезис 1>", "<ключевой тезис 2>", ...],
  "decisions": ["<решение/вывод 1>", "<решение/вывод 2>", ...],
  "open_questions": ["<открытый вопрос 1>", ...],
  "next_steps": ["<следующий шаг 1>", ...],
  "mood": "<тональность диалога: деловая / дружеская / техническая / обучающая / смешанная>",
  "summary": "<краткое резюме всего разговора, 3-5 предложений>",
  "image_prompt": "<одна короткая фраза на английском для генерации изображения по теме: сцена, стиль (digital art, minimalist, illustration), настроение. Без людей, политики, брендов. Пример: full moon over lake at night, minimalist digital art, serene>"
}

Если какой-либо раздел пуст — оставь пустой список []. Поле image_prompt — обязательно заполни по теме разговора.
Ответь ТОЛЬКО JSON, ничего больше.
"""


def _format_history_as_text(history: list[dict[str, str]]) -> str:
    """Convert list of {role, content} to readable dialog text."""
    lines: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            label = "Пользователь"
        elif role == "assistant":
            label = "Ассистент"
        else:
            label = role
        lines.append(f"{label}: {content}")
    return "\n\n".join(lines)


def _parse_llm_json(raw: str) -> dict:
    """Extract and parse JSON from LLM response (handles markdown code blocks)."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON object from text
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Не удалось распарсить JSON из ответа LLM: {raw[:200]}")


def _ensure_dirs() -> None:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def analyze_conversation(
    telegram_id: int,
    model: str | None = None,
) -> dict:
    """
    Send conversation history to LLM and get structured JSON summary.

    Returns:
        dict with keys: topic, key_points, decisions, open_questions, next_steps, mood, summary
    Raises:
        ValueError: if history is empty or LLM returns invalid JSON.
    """
    history = ctx_svc.get_history(telegram_id)
    # Filter out summary injections
    dialog_messages = [m for m in history if not m["content"].startswith("[Краткое резюме")]

    if not dialog_messages:
        raise ValueError("История разговора пуста. Поговори со мной сначала — потом создадим отчёт!")

    dialog_text = _format_history_as_text(dialog_messages)

    if not model:
        model = get_user_model(telegram_id) or "openrouter"

    logger.info(
        "report_analyze_started",
        extra={
            "event": "report_analyze_started",
            "telegram_id": telegram_id,
            "messages_count": len(dialog_messages),
            "model": model,
        },
    )

    raw_response, _ = get_chat_response(
        user_message=dialog_text,
        model=model,
        system_message=REPORT_SYSTEM_PROMPT,
        telegram_id=telegram_id,
    )

    data = _parse_llm_json(raw_response)

    # Guarantee all expected keys exist
    defaults = {
        "topic": "Не определена",
        "key_points": [],
        "decisions": [],
        "open_questions": [],
        "next_steps": [],
        "mood": "не определена",
        "summary": "",
        "image_prompt": "",
    }
    for key, default in defaults.items():
        data.setdefault(key, default)

    logger.info(
        "report_analyze_done",
        extra={"event": "report_analyze_done", "telegram_id": telegram_id},
    )

    return data


def _generate_report_image(
    prompt: str,
    telegram_id: int,
    ts: str,
) -> str | None:
    """
    Generate image via OpenAI DALL-E 2 (1024x1024 — хорошее качество ~$0.020).
    Returns absolute path to saved PNG or None on error.
    """
    import base64

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not (prompt or "").strip():
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=api_key)
    try:
        resp = client.images.generate(
            model="dall-e-2",
            prompt=prompt.strip()[:1000],
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
    except Exception as e:
        logger.warning(
            "report_image_gen_failed",
            extra={"event": "report_image_gen_failed", "telegram_id": telegram_id, "error": str(e)},
        )
        return None

    b64 = getattr(resp.data[0], "b64_json", None) if resp.data else None
    if not b64:
        return None

    filename = f"report_{telegram_id}_{ts}_cover.png"
    image_path = os.path.join(REPORTS_DIR, filename)
    try:
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(b64))
        return os.path.abspath(image_path)
    except Exception as e:
        logger.warning(
            "report_image_save_failed",
            extra={"event": "report_image_save_failed", "path": image_path, "error": str(e)},
        )
        return None


def generate_report(telegram_id: int, model: str | None = None) -> str:
    """
    Full pipeline: history → LLM analysis → HTML → PDF.

    Returns:
        Absolute path to the generated PDF file.
    Raises:
        ValueError: if history is empty.
        ImportError: if jinja2 or weasyprint are not installed.
        Exception: on any other error.
    """
    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML as WeasyHTML
    except ImportError as e:
        raise ImportError(
            f"Для генерации PDF нужны jinja2 и weasyprint. Установи: pip install jinja2 weasyprint\n{e}"
        ) from e

    _ensure_dirs()

    data = analyze_conversation(telegram_id, model=model)
    data["generated_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Generate image (DALL-E 2, 1024x1024 — лучше качество ~$0.020)
    image_prompt = (data.get("image_prompt") or "").strip()
    image_path = _generate_report_image(image_prompt, telegram_id, ts) if image_prompt else None
    data["image_url"] = str(Path(image_path).as_uri()) if image_path else None

    # Render HTML template
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template("report_template.html")
    html_content = template.render(**data)

    # Generate PDF
    pdf_filename = f"report_{telegram_id}_{ts}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    logger.info(
        "report_pdf_generating",
        extra={"event": "report_pdf_generating", "path": pdf_path},
    )

    WeasyHTML(string=html_content, base_url=TEMPLATES_DIR).write_pdf(pdf_path)

    logger.info(
        "report_pdf_done",
        extra={"event": "report_pdf_done", "path": pdf_path, "telegram_id": telegram_id},
    )

    return pdf_path
