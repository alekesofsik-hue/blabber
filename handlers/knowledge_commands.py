"""
Knowledge base commands — /kb and document upload handler.

Manages long-term knowledge base (memory C / RAG).  Users upload documents;
the bot indexes them and retrieves relevant fragments when answering questions.
"""

from __future__ import annotations

import telebot
from telebot import types

from middleware.auth import with_user_check
import services.knowledge_service as kb_svc
from user_storage import is_kb_enabled, set_kb_enabled

SUPPORTED_EXTS = {"txt", "pdf", "docx", "doc", "md"}
REINDEX_MODES = {"embeddings", "summary", "all"}


def _doc_status_badges(doc: dict) -> str:
    badges: list[str] = []
    parser_backend = doc.get("parser_backend")
    if parser_backend == "docling":
        badges.append("docling")
    elif parser_backend == "legacy":
        badges.append("legacy")

    summary_status = str(doc.get("summary_status") or "").strip().lower()
    if summary_status == "generated":
        badges.append("summary")
    elif summary_status == "fallback_preview":
        badges.append("preview")

    if doc.get("doc_has_tables"):
        badges.append("tables")
    if doc.get("doc_has_headings"):
        badges.append("sections")

    if not badges:
        return ""
    return " [" + ", ".join(badges) + "]"


def register_knowledge_handlers(bot: telebot.TeleBot) -> None:

    # ── /kb ───────────────────────────────────────────────────────────────────

    @bot.message_handler(commands=["kb"])
    @with_user_check(bot)
    def handle_kb(message):
        user_id = message.from_user.id
        parts = message.text.split()

        if len(parts) >= 2:
            arg = parts[1].lower()

            if arg == "on":
                set_kb_enabled(user_id, True)
                bot.send_message(
                    message.chat.id,
                    "📚 <b>База знаний включена!</b>\n\n"
                    "Теперь при ответах я буду искать релевантные фрагменты "
                    "из твоих документов и использовать их как источник фактов.",
                    parse_mode="HTML",
                )
                return

            if arg == "off":
                set_kb_enabled(user_id, False)
                bot.send_message(
                    message.chat.id,
                    "📚 База знаний выключена.\n\n"
                    "Включить обратно: /kb on",
                )
                return

            if arg == "clear":
                kb_svc.clear_all(user_id)
                set_kb_enabled(user_id, False)
                bot.send_message(
                    message.chat.id,
                    "🗑 База знаний полностью очищена.\n\n"
                    "🧹 Контекст текущего чата тоже сброшен, чтобы я не тянул факты из удалённых документов.",
                )
                return

            if arg == "reindex":
                target = "all"
                mode = "embeddings"
                dry_run = False
                extra = [part.strip().lower() for part in parts[2:]]
                if extra:
                    if extra[0] in REINDEX_MODES | {"dry-run", "dryrun"}:
                        pass
                    else:
                        target = extra.pop(0)
                for item in extra:
                    if item in {"dry-run", "dryrun"}:
                        dry_run = True
                    elif item in REINDEX_MODES:
                        mode = item
                wait_msg = bot.send_message(
                    message.chat.id,
                    "⏳ Переиндексирую KB по уже сохранённым фрагментам...",
                )

                if target == "all":
                    ok, result_msg = kb_svc.reindex_all_documents(user_id, mode=mode, dry_run=dry_run)
                else:
                    try:
                        doc_id = int(target)
                    except ValueError:
                        bot.edit_message_text(
                            "❌ Использование: /kb reindex [all|<id>] [embeddings|summary|all] [dry-run]\n"
                            "Посмотреть id можно в списке /kb.",
                            message.chat.id,
                            wait_msg.message_id,
                        )
                        return
                    ok, result_msg = kb_svc.reindex_document(user_id, doc_id, mode=mode, dry_run=dry_run)

                if ok:
                    bot.edit_message_text(
                        f"✅ <b>Переиндексация завершена</b>\n\n"
                        f"{result_msg}\n\n"
                        "Управление: /kb",
                        message.chat.id,
                        wait_msg.message_id,
                        parse_mode="HTML",
                    )
                else:
                    bot.edit_message_text(
                        f"❌ Не получилось переиндексировать KB:\n{result_msg}",
                        message.chat.id,
                        wait_msg.message_id,
                    )
                return

            if arg == "url":
                if len(parts) < 3:
                    bot.send_message(
                        message.chat.id,
                        "🌐 <b>Как пользоваться /kb url</b>\n\n"
                        "Отправь ссылку так:\n"
                        "<code>/kb url https://example.com/article</code>\n\n"
                        "Я загружу страницу, превращу её в текст и добавлю в твою базу знаний.",
                        parse_mode="HTML",
                    )
                    return

                url = parts[2].strip()
                wait_msg = bot.send_message(
                    message.chat.id,
                    "⏳ Загружаю страницу и добавляю её в базу знаний...",
                )
                ok, result_msg = kb_svc.index_url(user_id, url)
                if ok:
                    kb_note = ""
                    if not is_kb_enabled(user_id):
                        set_kb_enabled(user_id, True)
                        kb_note = "\n\n✅ База знаний автоматически включена."
                    bot.edit_message_text(
                        f"✅ <b>Страница добавлена в базу знаний!</b>\n"
                        f"📄 {result_msg}{kb_note}\n\n"
                        "Теперь можно задавать вопросы по этой странице.\n"
                        "Управление: /kb",
                        message.chat.id,
                        wait_msg.message_id,
                        parse_mode="HTML",
                    )
                else:
                    bot.edit_message_text(
                        f"❌ Не получилось добавить страницу:\n{result_msg}",
                        message.chat.id,
                        wait_msg.message_id,
                    )
                return

        _send_kb_status(bot, message.chat.id, user_id)

    # ── Inline callbacks ──────────────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("kb_"))
    def callback_kb(call):
        user_id = call.from_user.id
        data = call.data

        if data == "kb_toggle":
            new_state = not is_kb_enabled(user_id)
            set_kb_enabled(user_id, new_state)
            label = "включена" if new_state else "выключена"
            bot.answer_callback_query(call.id, f"База знаний {label}")
            _refresh_kb_status(bot, call)
            return

        if data.startswith("kb_del_"):
            try:
                doc_id = int(data.split("_", 2)[2])
            except (IndexError, ValueError):
                bot.answer_callback_query(call.id, "Ошибка.")
                return
            ok, msg = kb_svc.delete_document(user_id, doc_id)
            bot.answer_callback_query(call.id, msg)
            _refresh_kb_status(bot, call)
            return

        if data == "kb_clear_all":
            kb_svc.clear_all(user_id)
            set_kb_enabled(user_id, False)
            bot.answer_callback_query(call.id, "KB очищена, контекст чата сброшен")
            _refresh_kb_status(bot, call)
            return

    # ── Document upload ───────────────────────────────────────────────────────

    @bot.message_handler(content_types=["document"])
    @with_user_check(bot)
    def handle_document(message):
        user_id = message.from_user.id
        doc = message.document
        filename = doc.file_name or "document"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in SUPPORTED_EXTS:
            bot.send_message(
                message.chat.id,
                f"📎 Получен файл <b>{filename}</b>, но этот тип не поддерживается.\n\n"
                f"Поддерживаемые форматы: TXT, PDF, DOC, DOCX, MD\n\n"
                "Управление базой знаний: /kb",
                parse_mode="HTML",
            )
            return

        max_doc_size_bytes = kb_svc.get_max_doc_size_bytes()
        if doc.file_size and doc.file_size > max_doc_size_bytes:
            bot.send_message(
                message.chat.id,
                f"❌ Файл слишком большой (макс. {kb_svc.format_doc_size_limit(max_doc_size_bytes)}).",
            )
            return

        wait_msg = bot.send_message(
            message.chat.id,
            f"⏳ Добавляю <b>{filename}</b> в базу знаний...",
            parse_mode="HTML",
        )

        try:
            file_info = bot.get_file(doc.file_id)
            data = bot.download_file(file_info.file_path)
        except Exception as e:
            bot.edit_message_text(
                "❌ Не удалось скачать файл из Telegram.\n"
                "Попробуй отправить его ещё раз.",
                message.chat.id,
                wait_msg.message_id,
            )
            return

        ok, result_msg = kb_svc.index_document(user_id, filename, data)

        if ok:
            final_msg = result_msg
            if not is_kb_enabled(user_id):
                set_kb_enabled(user_id, True)
                final_msg += "\n\n✅ База знаний автоматически включена."

            bot.edit_message_text(
                final_msg,
                message.chat.id,
                wait_msg.message_id,
                parse_mode="HTML",
            )
        else:
            bot.edit_message_text(
                f"❌ Не получилось добавить <b>{filename}</b>.\n\n"
                f"{result_msg}\n\n"
                "Попробуй загрузить файл ещё раз или проверь формат через /kb.",
                message.chat.id,
                wait_msg.message_id,
                parse_mode="HTML",
            )


# ── Status helpers ────────────────────────────────────────────────────────────

def _build_kb_message(user_id: int) -> tuple[str, types.InlineKeyboardMarkup]:
    docs = kb_svc.get_documents(user_id)
    enabled = is_kb_enabled(user_id)
    status_icon = "✅" if enabled else "⏸"

    text = (
        f"📚 <b>База знаний</b>\n\n"
        f"Статус: {status_icon} {'включена' if enabled else 'выключена'}\n"
        f"Документов: {len(docs)} / {kb_svc.MAX_DOCS_PER_USER}\n\n"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)
    toggle_label = "⏸ Выключить" if enabled else "✅ Включить"
    kb.add(types.InlineKeyboardButton(toggle_label, callback_data="kb_toggle"))

    if docs:
        text += "<b>Документы:</b>\n"
        for doc in docs:
            size_kb = max(1, doc["size_bytes"] // 1024)
            icon = "🌐" if doc.get("source_type") == "url" else "📄"
            text += (
                f"• {icon} <code>id {doc['id']}</code> — {doc['name']} "
                f"({size_kb} КБ, {doc['chunk_count']} фрагм.)"
                f"{_doc_status_badges(doc)}\n"
            )
            short_name = doc["name"][:35] + ("…" if len(doc["name"]) > 35 else "")
            kb.add(types.InlineKeyboardButton(
                f"🗑 {icon} #{doc['id']} {short_name}",
                callback_data=f"kb_del_{doc['id']}",
            ))
        kb.add(types.InlineKeyboardButton("🗑 Удалить все документы", callback_data="kb_clear_all"))
    else:
        text += (
            "Пока нет документов.\n\n"
            "Загрузи любой файл (TXT, PDF, DOC, DOCX, MD) прямо в чат или добавь страницу через "
            "<code>/kb url https://...</code> — я проиндексирую её и буду отвечать на вопросы!"
        )

    text += (
        "\n\n<i>Команды: /kb on · /kb off · /kb clear · /kb url https://... · "
        "/kb reindex [all|id] [embeddings|summary|all] [dry-run]\n"
        "dry-run — отдельный флаг предварительного просмотра без изменений\n"
        "id документа смотри в списке выше.\n"
        "Просто пришли файл — он добавится автоматически</i>"
    )

    return text, kb


def _send_kb_status(bot: telebot.TeleBot, chat_id: int, user_id: int) -> None:
    text, kb = _build_kb_message(user_id)
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)


def _refresh_kb_status(bot: telebot.TeleBot, call) -> None:
    text, kb = _build_kb_message(call.from_user.id)
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception:
        pass
