"""
Quote commands — /quote, /quotes.

Users build a personal collection of funny/interesting phrases from the bot.
Semantic search powered by LanceDB + OpenAI embeddings; falls back to
keyword search when embeddings are unavailable.

Commands:
  /quote <фраза>         — сохранить фразу вручную
  /quotes                — случайная фраза из коллекции
  /quotes list           — вся коллекция (по 3 на страницу; кнопки 🗑 1–3)
  /quotes search <текст> — семантический поиск по смыслу
  /quotes del номер      — удалить по id из списка (см. подпись «id …»)
  /quotes clear          — очистить всю коллекцию
  /quotes help           — справка
"""

from __future__ import annotations

import html
import logging
import re
from html import unescape

import telebot
from telebot import types

from middleware.auth import with_user_check
import services.quotes_service as quotes_svc

logger = logging.getLogger("blabber")


def _normalize_command_text(text: str | None) -> str:
    """
    Telegram/clients sometimes insert NBSP or BOM; strip so /quotes list parses reliably.
    """
    if not text:
        return ""
    t = text.replace("\u00a0", " ").replace("\u2009", " ").replace("\u202f", " ")
    return t.lstrip("\ufeff\u200e\u200f")


def _first_command_token(normalized: str) -> str:
    """First token, lowercased, e.g. '/quotes' or '/quote'."""
    if not normalized.startswith("/"):
        return ""
    return normalized.split()[0].split("@")[0].lower()


def _is_quote_command(message) -> bool:
    """Match /quote (not /quotes) — use func= instead of commands= for robust parsing."""
    if message.content_type != "text" or not message.text:
        return False
    t = _normalize_command_text(message.text)
    return _first_command_token(t) == "/quote"


def _is_quotes_command(message) -> bool:
    """Match /quotes and /quotes … — not /quote."""
    if message.content_type != "text" or not message.text:
        return False
    t = _normalize_command_text(message.text)
    return _first_command_token(t) == "/quotes"


def register_quote_handlers(bot: telebot.TeleBot) -> None:

    # ── /quote <текст> — сохранить фразу ─────────────────────────────────────

    @bot.message_handler(func=_is_quote_command)
    @with_user_check(bot)
    def handle_quote_add(message):
        """Сохранить фразу в коллекцию."""
        user_id = message.from_user.id
        parts = _normalize_command_text(message.text).split(maxsplit=1)

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "😄 <b>Как сохранить фразу</b>\n\n"
                "Напиши фразу, которую сказал Балабол — и она попадёт в твою коллекцию.\n\n"
                "<b>Пример:</b>\n"
                "/quote Я не баг — я фича с характером!\n\n"
                "Потом найти по смыслу:\n"
                "/quotes search ошибки\n\n"
                "Или случайную:\n"
                "/quotes\n\n"
                "Вся коллекция и управление: /quotes list",
                parse_mode="HTML",
            )
            return

        text = parts[1].strip()
        ok, msg = quotes_svc.add_quote(user_id, text)
        emoji = "😄" if ok else "❌"
        bot.send_message(message.chat.id, f"{emoji} {msg}")

    # ── /quotes — основная команда управления коллекцией ─────────────────────

    @bot.message_handler(func=_is_quotes_command)
    @with_user_check(bot)
    def handle_quotes(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        parts = _normalize_command_text(message.text).split(maxsplit=1)

        # /quotes без аргументов — случайная фраза
        if len(parts) < 2:
            _send_random(bot, chat_id, user_id)
            return

        arg = parts[1].strip()
        sub, *rest = arg.split(maxsplit=1)
        sub = sub.strip().lower()
        tail = (rest[0] if rest else "").strip()

        if sub == "list":
            _send_list_page(bot, chat_id, user_id, page=0)

        elif sub == "random":
            _send_random(bot, chat_id, user_id)

        elif sub == "search":
            if not tail:
                bot.send_message(
                    chat_id,
                    "🔍 Укажи что искать.\n"
                    "Пример: /quotes search смерть",
                )
                return
            _send_search(bot, chat_id, user_id, tail)

        elif sub == "del":
            if not tail or not tail.strip().isdigit():
                bot.send_message(chat_id, "❌ Укажи номер фразы: /quotes del 3")
                return
            quote_id = int(tail.strip())
            ok, msg = quotes_svc.delete_quote(user_id, quote_id)
            emoji = "🗑" if ok else "❌"
            bot.send_message(chat_id, f"{emoji} {msg}")

        elif sub == "clear":
            count = quotes_svc.get_count(user_id)
            if count == 0:
                bot.send_message(chat_id, "📭 Коллекция уже пуста.")
                return
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                types.InlineKeyboardButton(
                    "🗑 Да, очистить",
                    callback_data=f"quotes_clear_yes_{user_id}",
                ),
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"quotes_clear_no_{user_id}",
                ),
            )
            bot.send_message(
                chat_id,
                f"🗑 Удалить все {count} фраз из коллекции? Это нельзя отменить.",
                reply_markup=kb,
            )

        elif sub == "help":
            _send_help(bot, chat_id)

        else:
            # Неизвестный аргумент — пробуем как поиск
            _send_search(bot, chat_id, user_id, arg)

    # ── Callback: list pagination ─────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("quotes_pg_"))
    def callback_quotes_page(call):
        user_id = call.from_user.id
        try:
            page = int(call.data.split("_", 2)[2])
        except (ValueError, TypeError, IndexError):
            bot.answer_callback_query(call.id, "Ошибка.")
            return
        text, kb = _build_list_page(user_id, page)
        if kb is None:
            bot.answer_callback_query(call.id, "Список пуст.")
            try:
                bot.edit_message_text(
                    "📭 Коллекция пуста.\n\nДобавь фразу: /quote текст_фразы",
                    call.message.chat.id,
                    call.message.message_id,
                )
            except Exception:
                pass
            return
        bot.answer_callback_query(call.id, f"Стр. {page + 1}")
        try:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb,
            )
        except Exception as exc:
            logger.warning("quotes_page_edit_failed", extra={"error": str(exc)[:200]})

    # ── Callback: delete one quote from list ──────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("quotes_rm_"))
    def callback_quotes_remove(call):
        user_id = call.from_user.id
        data = call.data
        # quotes_rm_{qid}_{page}
        try:
            parts = data.split("_")
            quote_id = int(parts[2])
            page = int(parts[3])
        except (ValueError, IndexError):
            bot.answer_callback_query(call.id, "Ошибка.")
            return

        ok, msg = quotes_svc.delete_quote(user_id, quote_id)
        bot.answer_callback_query(call.id, msg[:200])

        if not ok:
            return

        _, total, _, cur = quotes_svc.list_page(user_id, page)
        if total == 0:
            try:
                bot.edit_message_text(
                    "📭 Коллекция пуста.\n\nДобавь фразу: /quote текст_фразы",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None,
                )
            except Exception:
                pass
            return

        text, kb = _build_list_page(user_id, cur)
        if kb is None:
            return
        try:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb,
            )
        except Exception as exc:
            logger.warning("quotes_rm_edit_failed", extra={"error": str(exc)[:200]})

    # ── Callback: confirm clear ───────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("quotes_clear_"))
    def callback_quotes_clear(call):
        parts = call.data.split("_")
        action = parts[2]  # "yes" or "no"
        try:
            owner_id = int(parts[3])
        except (IndexError, ValueError):
            bot.answer_callback_query(call.id, "Ошибка.")
            return

        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "Это не твоя кнопка.", show_alert=True)
            return

        if action == "yes":
            ok, msg = quotes_svc.clear_all(call.from_user.id)
            bot.answer_callback_query(call.id, msg)
            try:
                bot.edit_message_text(
                    f"✅ {msg}",
                    call.message.chat.id,
                    call.message.message_id,
                )
            except Exception:
                pass
        else:
            bot.answer_callback_query(call.id, "Отмена.")
            try:
                bot.edit_message_text(
                    "❌ Очистка отменена. Коллекция сохранена.",
                    call.message.chat.id,
                    call.message.message_id,
                )
            except Exception:
                pass


# ── Helper renderers ──────────────────────────────────────────────────────────

def _send_random(bot: telebot.TeleBot, chat_id: int, user_id: int) -> None:
    quote = quotes_svc.get_random(user_id)
    if not quote:
        bot.send_message(
            chat_id,
            "📭 Коллекция пуста.\n\n"
            "Сохрани первую смешную фразу Балабола:\n"
            "/quote текст_фразы",
        )
        return

    count = quotes_svc.get_count(user_id)
    safe = html.escape(quote["text"] or "")
    bot.send_message(
        chat_id,
        f"😄 <b>Случайная фраза из коллекции</b>\n\n"
        f"«{safe}»\n\n"
        f"<i>Всего в коллекции: {count}</i>",
        parse_mode="HTML",
    )


def _quote_html_block(raw: str) -> str:
    """Полный текст цитаты для HTML: экранирование + переносы строк как <br/>."""
    body = html.escape(raw or "")
    return body.replace("\n", "<br/>")


def _build_list_page(user_id: int, page: int) -> tuple[str, types.InlineKeyboardMarkup | None]:
    """
    Текст + клавиатура для страницы списка цитат.
    Полные цитаты в теле сообщения; кнопки только «🗑» + номер строки (без дублирования текста).
    Если коллекция пуста — ("", None).
    """
    items, total, total_pages, cur_page = quotes_svc.list_page(user_id, page)
    if total == 0:
        return "", None

    ps = quotes_svc.LIST_PAGE_SIZE
    lines = [
        f"😄 <b>Мои цитаты</b> — всего {total}",
        f"<i>Страница {cur_page + 1} из {total_pages}</i>\n",
    ]
    for i, q in enumerate(items):
        gnum = cur_page * ps + i + 1
        raw = q.get("text") or ""
        body = _quote_html_block(raw)
        added = str(q.get("added_at") or "")[:10]
        lines.append(f"{gnum}. {body}")
        lines.append(f"   <i>id {q['id']} • {html.escape(added)}</i>")

    lines.append(
        "\n🔍 /quotes search ваш_запрос · <b>Удалить:</b> кнопки 🗑 с номером строки выше или /quotes del номер"
    )

    text_out = "\n".join(lines)
    # Редкий случай: даже 3×1000 символов + HTML > 4096 — слегка ужимаем длинные цитаты
    if len(text_out) > 4000:
        lines = [
            f"😄 <b>Мои цитаты</b> — всего {total}",
            f"<i>Страница {cur_page + 1} из {total_pages}</i>\n",
        ]
        cap = 850
        for i, q in enumerate(items):
            gnum = cur_page * ps + i + 1
            raw = q.get("text") or ""
            if len(raw) > cap:
                raw = raw[:cap] + "…"
            body = _quote_html_block(raw)
            added = str(q.get("added_at") or "")[:10]
            lines.append(f"{gnum}. {body}")
            lines.append(f"   <i>id {q['id']} • {html.escape(added)}</i>")
        lines.append(
            "\n<i>Текст на странице урезан из‑за лимита Telegram (4096 символов).</i>\n"
            "\n🔍 /quotes search · Удалить: 🗑 по номеру или /quotes del номер"
        )
        text_out = "\n".join(lines)

    kb = types.InlineKeyboardMarkup(row_width=3)
    row_btns: list[types.InlineKeyboardButton] = []
    for i, q in enumerate(items, start=1):
        qid = q["id"]
        row_btns.append(
            types.InlineKeyboardButton(
                f"🗑 {i}",
                callback_data=f"quotes_rm_{qid}_{cur_page}",
            )
        )
    if row_btns:
        kb.row(*row_btns)

    nav: list[types.InlineKeyboardButton] = []
    if cur_page > 0:
        nav.append(
            types.InlineKeyboardButton("◀️ Назад", callback_data=f"quotes_pg_{cur_page - 1}")
        )
    if cur_page < total_pages - 1:
        nav.append(
            types.InlineKeyboardButton("Вперёд ▶️", callback_data=f"quotes_pg_{cur_page + 1}")
        )
    if nav:
        kb.row(*nav)

    return text_out, kb


def _send_list_page(bot: telebot.TeleBot, chat_id: int, user_id: int, page: int = 0) -> None:
    text_out, kb = _build_list_page(user_id, page)
    if kb is None:
        bot.send_message(
            chat_id,
            "📭 Коллекция пуста.\n\n"
            "Добавь первую смешную фразу:\n"
            "/quote текст_фразы",
        )
        return
    try:
        bot.send_message(chat_id, text_out, parse_mode="HTML", reply_markup=kb)
    except Exception as exc:
        logger.warning("quotes_list_send_failed", extra={"error": str(exc)[:200]})
        plain = unescape(re.sub(r"<[^>]+>", "", text_out))
        bot.send_message(chat_id, plain, reply_markup=kb)


def _send_search(bot: telebot.TeleBot, chat_id: int, user_id: int, query: str) -> None:
    total = quotes_svc.get_count(user_id)
    if total == 0:
        bot.send_message(
            chat_id,
            "📭 Коллекция пуста. Добавь фразы командой /quote текст_фразы",
        )
        return

    results, mode = quotes_svc.search(user_id, query)

    if not results:
        bot.send_message(
            chat_id,
            f"🔍 По запросу «{query}» ничего не найдено.\n\n"
            "Попробуй другой запрос или посмотри /quotes list",
        )
        return

    shown = len(results)
    if mode == "semantic":
        mode_line = "по смыслу (семантика)"
    else:
        mode_line = "по словам (подстрока в тексте)"

    lines = [
        f"🔍 <b>Поиск:</b> «{html.escape(query)}»\n",
        f"<i>Режим: {mode_line} · в коллекции: {total} · показано: {shown}</i>\n",
    ]

    if mode == "semantic" and results:
        first = results[0]
        fl = first.get("closeness_label") or ""
        lines.append(
            f"💡 <i>Лучший в списке: {html.escape(fl)} — относительно твоего запроса.</i>\n"
        )

    for i, r in enumerate(results, start=1):
        text = r.get("text", "")
        short = text[:120] + ("…" if len(text) > 120 else "")
        lines.append(f"{i}. {html.escape(short)}")

        if mode == "semantic":
            qid = r.get("id")
            added = str(r.get("added_at") or "")[:10]
            pct = r.get("closeness_pct")
            dist = r.get("distance")
            lbl = r.get("closeness_label") or ""
            id_part = f"id {qid}" if qid is not None else "id ?"
            date_part = html.escape(added) if added else "дата ?"
            lines.append(
                "   <i>"
                f"{id_part} · {date_part} · ~{pct}% · {html.escape(lbl)} · "
                f"d≈{float(dist):.3f}"
                "</i>"
            )
        else:
            qid = r.get("id")
            added = str(r.get("added_at") or "")[:10]
            id_part = f"id {qid}" if qid is not None else "id ?"
            date_part = html.escape(added) if added else "—"
            lines.append(
                f"   <i>{id_part} · {date_part} · совпадение по подстроке</i>"
            )

    if mode == "semantic":
        lines.append(
            "\n<i>«d» — метрика векторного поиска (меньше = ближе). "
            "~% — условная наглядность, не точная вероятность.</i>"
        )

    text_out = "\n".join(lines)
    try:
        bot.send_message(chat_id, text_out, parse_mode="HTML")
    except Exception as exc:
        logger.warning("quotes_search_send_failed", extra={"error": str(exc)[:200]})
        plain = unescape(re.sub(r"<[^>]+>", "", text_out))
        bot.send_message(chat_id, plain)


def _send_help(bot: telebot.TeleBot, chat_id: int) -> None:
    # Угловые скобки в плейсхолдерах (<фраза>) ломают Telegram HTML — только валидные теги или &lt;…&gt;
    text = (
        "😄 <b>Коллекция смешных фраз Балабола</b>\n\n"
        "Балабол иногда выдаёт золото. Сохрани это!\n\n"
        "<b>Сохранить:</b>\n"
        "/quote текст_фразы — сохранить фразу вручную\n\n"
        "<b>Просмотр:</b>\n"
        "/quotes — случайная фраза\n"
        "/quotes list — все страницы (до <b>3</b> полных цитат на страницу; "
        "кнопки <b>🗑 1</b>, <b>🗑 2</b>, <b>🗑 3</b> — удалить строку с тем же номером)\n"
        "/quotes random — ещё одна случайная\n\n"
        "<b>Поиск по смыслу:</b>\n"
        "/quotes search ваш_запрос\n"
        "Пример: /quotes search грусть\n"
        "→ Найдёт фразы <i>по смыслу</i>, не только по словам!\n\n"
        "<b>Удалить:</b>\n"
        "В списке — кнопки 🗑 по номеру строки или /quotes del номер "
        "(номер из подписи <code>id …</code> под цитатой)\n"
        "/quotes clear — очистить всю коллекцию\n\n"
        "<i>Поиск по смыслу работает с OpenAI ключом. "
        "Без него — поиск по словам.</i>"
    )
    try:
        bot.send_message(chat_id, text, parse_mode="HTML")
    except Exception as exc:
        logger.warning("quotes_help_send_failed", extra={"error": str(exc)[:200]})
        bot.send_message(chat_id, re.sub(r"<[^>]+>", "", text))
