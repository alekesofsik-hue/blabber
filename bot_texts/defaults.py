"""
Встроенные шаблоны сообщений /start и /help (HTML для Telegram).

Правки текста для пользователей — в основном здесь. После изменений перезапуск бота
не обязателен, если не переопределено в БД (config): пустое `welcome_message` /
`help_message` = этот файл.

Плейсхолдер в welcome: {model} — подставляется название текущей модели (экранируется
во встроенном HTML-режиме).

Справка должна совпадать с фактическими командами в `bot.py` и `handlers/`
(в т.ч. `/agent`, `/duel`, `/compare_headlines`, `/admin`).
"""

from __future__ import annotations

import html
from typing import Any

# Единственный плейсхолдер для /start (встроенный HTML-шаблон)
START_MESSAGE_HTML_TEMPLATE = (
    "Привет! Я <b>Blabber</b> — балабол, который любит трепаться и болтать! 😄\n\n"
    "Отвечаю через разные модели: "
    "<b>GigaChat</b>, <b>OpenRouter</b> (DeepSeek), <b>DeepSeek R1</b>, "
    "<b>OpenAI</b>, <b>Yandex GPT</b>, <b>Ollama</b>.\n\n"
    "📌 <b>Быстрый обзор</b>\n"
    "• <code>/help</code> — полная справка по командам\n"
    "• <code>/models</code> и <code>/model</code> — список и выбор модели\n"
    "• <code>/role</code> — стиль бота (персона)\n"
    "• <code>/mode</code> — чат с памятью или вопрос-ответ\n"
    "• <code>/reset</code> или <code>/clear</code> — очистить историю чата\n"
    "• <code>/voice</code> — озвучка ответов\n\n"
    "🧠 <b>Память</b>\n"
    "<code>/remember</code>, <code>/prefer</code>, <code>/profile</code> — факты и предпочтения\n"
    "<code>/memory</code> — автоподсказки, что запомнить (с подтверждением)\n\n"
    "😄 <b>Цитаты</b>\n"
    "<code>/quote</code> — сохранить фразу · <code>/quotes</code> — случайная\n"
    "<code>/quotes list</code> — вся коллекция (до 3 на стр., кнопки 🗑 1–3)\n"
    "<code>/quotes search</code> — поиск по смыслу · <code>/quotes help</code> — справка по коллекции\n\n"
    "📚 <code>/kb</code> — база знаний; пришли файл (TXT, PDF, DOCX, MD) в чат\n"
    "🕵️ <b>Балабол-новостник:</b> <code>/agent</code> — статус и кнопки; "
    "<code>/agent on</code> — режим с поиском по RSS и Hacker News; "
    "<code>/duel</code> или <code>/compare_headlines</code> — сравнить два свежих заголовка из "
    "<b>разных</b> лент (нужен <code>/agent on</code>)\n"
    "📄 <code>/report</code> — PDF по разговору (нужны <code>/mode chat</code> и история) · "
    "<code>/report help</code> — подробности\n\n"
    "🤖 <b>Сейчас выбрана модель:</b> {model}"
)

HELP_MESSAGE_HTML = (
    "📚 <b>Полная справка по командам</b>\n\n"
    "<b>Общее</b>\n"
    "<code>/start</code> — приветствие и краткая карта\n"
    "<code>/help</code> — эта справка\n"
    "<code>/admin</code> — панель администратора (только при наличии прав)\n\n"
    "<b>Модели</b>\n"
    "<code>/models</code> — список и текущая модель\n"
    "<code>/model</code> — переключить. Примеры:\n"
    "<code>/model gigachat</code> · <code>/model openrouter</code> · "
    "<code>/model reasoning</code> · <code>/model openai</code> · "
    "<code>/model yandexgpt</code> · <code>/model ollama</code>\n\n"
    "<b>Роль и режим</b>\n"
    "<code>/role</code> — текущая роль и меню (assistant, developer, analyst, teacher, writer…)\n"
    "<code>/mode</code> — без аргументов: меню. "
    "<code>/mode chat</code> — чат с памятью (окно реплик + резюме). "
    "<code>/mode single</code> — каждый запрос отдельно\n\n"
    "<b>История чата</b>\n"
    "<code>/reset</code> или <code>/clear</code> — очистить историю (с подтверждением; только в режиме чата)\n\n"
    "<b>Озвучка</b>\n"
    "<code>/voice</code> — статус\n"
    "<code>/voice on</code> / <code>/voice off</code>\n"
    "<code>/voice alena</code> / <code>/voice filipp</code>\n\n"
    "<b>Память: факты и предпочтения</b>\n"
    "<code>/remember</code> текст — факт о тебе (в каждый запрос к модели)\n"
    "<code>/prefer</code> текст — как отвечать (стиль, ограничения)\n"
    "<code>/profile</code> — список и удаление\n\n"
    "<b>Автопамять</b>\n"
    "<code>/memory</code> — статус\n"
    "<code>/memory on</code> / <code>/memory off</code> — подсказки «что запомнить» "
    "(сохранение только по кнопке)\n\n"
    "<b>Коллекция смешных фраз</b>\n"
    "<code>/quote</code> текст — сохранить цитату\n"
    "<code>/quotes</code> — случайная · <code>/quotes random</code> — ещё одна\n"
    "<code>/quotes list</code> — все страницы (до <b>3</b> цитат на стр.; кнопки "
    "<b>🗑 1–3</b> по номеру строки)\n"
    "<code>/quotes search</code> запрос — по смыслу (нужен <code>OPENAI_API_KEY</code>; иначе по словам)\n"
    "<code>/quotes del</code> id — удалить по подписи <code>id …</code> под цитатой\n"
    "<code>/quotes clear</code> — очистить всю коллекцию\n"
    "<code>/quotes help</code> — подробнее про коллекцию\n\n"
    "<b>База знаний (RAG)</b>\n"
    "<code>/kb</code> — статус, документы, кнопки\n"
    "<code>/kb on</code> / <code>/kb off</code> / <code>/kb clear</code>\n"
    "Файл в чат (TXT, PDF, DOCX, MD) — индексация автоматически\n\n"
    "<b>Балабол-новостник (агент)</b>\n"
    "<code>/agent</code> — статус, список ключей источников, быстрые кнопки (заголовки без "
    "включения режима)\n"
    "<code>/agent on</code> / <code>/agent off</code> — включить или выключить агентный режим: "
    "модель сама вызывает инструменты (поиск по RSS, топ HN, чтение страницы по ссылке, "
    "сравнение двух заголовков из разных лент)\n"
    "<code>/duel</code> или <code>/compare_headlines</code> — то же через агент, но с "
    "заранее заданным запросом на один вызов <code>compare_two_headlines</code> "
    "(случайные две ленты или, например, <code>/duel habr meduza</code>; нужен "
    "<code>/agent on</code>)\n\n"
    "<b>Отчёт PDF</b>\n"
    "<code>/report</code> — отчёт по истории чата (нужны <code>/mode chat</code> и переписка)\n"
    "<code>/report help</code> — детали\n"
    "<i>Обложка в PDF — при настроенном <code>OPENAI_API_KEY</code>.</i>\n\n"
    "💰 Для OpenAI/OpenRouter в ответе показывается ориентировочная стоимость в рублях (ЦБ РФ).\n\n"
    "Просто напиши в чат — отвечу в характере Балабола! 😊"
)


def _built_in_start_html(model_label: str) -> str:
    safe = html.escape(model_label)
    return START_MESSAGE_HTML_TEMPLATE.format(model=safe)


def resolve_start_message(model_label: str, welcome_override: Any) -> tuple[str, str | None]:
    """
    Текст + parse_mode для /start.

    Если welcome_override непустой (из config `welcome_message`) — plain text,
    подстановка {model} без HTML-экранирования (для обратной совместимости с админкой).

    Иначе — встроенный HTML из START_MESSAGE_HTML_TEMPLATE.
    """
    if welcome_override is not None and str(welcome_override).strip():
        text = str(welcome_override).replace("{model}", model_label)
        return text, None
    return _built_in_start_html(model_label), "HTML"


def resolve_help_message(help_override: Any) -> tuple[str, str | None]:
    """
    Текст + parse_mode для /help.

    Непустой help_override (config `help_message`) — plain text без HTML.
    Иначе HELP_MESSAGE_HTML с parse_mode HTML.
    """
    if help_override is not None and str(help_override).strip():
        return str(help_override), None
    return HELP_MESSAGE_HTML, "HTML"
