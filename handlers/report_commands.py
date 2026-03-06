"""
Report commands — /report

Generates a PDF report based on the current conversation history.

Commands:
  /report        — generate PDF from conversation history and send it to user
  /report help   — show help message
"""

from __future__ import annotations

import logging
import os

import telebot

from middleware.auth import with_user_check
import services.context_service as ctx_svc

logger = logging.getLogger("blabber")

_HELP_TEXT = (
    "📄 <b>Генерация отчёта по разговору</b>\n\n"
    "Команда <code>/report</code> анализирует историю нашего с тобой разговора "
    "и создаёт структурированный PDF-отчёт.\n\n"
    "<b>Что войдёт в отчёт:</b>\n"
    "• Тема разговора\n"
    "• Обложка-картинка по теме (если настроен <code>OPENAI_API_KEY</code>)\n"
    "• Ключевые тезисы\n"
    "• Выводы и решения\n"
    "• Открытые вопросы\n"
    "• Следующие шаги\n\n"
    "<b>Условие:</b> контекст разговора должен быть включён "
    "(режим <code>chat</code>). Включить: /mode chat\n\n"
    "Просто напиши <code>/report</code> — и получишь PDF через несколько секунд."
)


def register_report_handlers(bot: telebot.TeleBot) -> None:

    @bot.message_handler(commands=["report"])
    @with_user_check(bot)
    def handle_report(message):
        user_id = message.from_user.id
        chat_id = message.chat.id

        parts = message.text.split(maxsplit=1)
        if len(parts) >= 2 and parts[1].strip().lower() == "help":
            bot.send_message(chat_id, _HELP_TEXT, parse_mode="HTML")
            return

        # Check that context mode is 'chat' and there is history
        mode = ctx_svc.get_mode(user_id)
        count = ctx_svc.get_message_count(user_id)

        if mode != "chat":
            bot.send_message(
                chat_id,
                "💬 <b>Режим чата не включён.</b>\n\n"
                "Чтобы создать отчёт, нужно:\n"
                "1. Включить режим чата: <code>/mode chat</code>\n"
                "2. Поговорить со мной\n"
                "3. Написать <code>/report</code>\n\n"
                "Подробнее: <code>/report help</code>",
                parse_mode="HTML",
            )
            return

        if count == 0:
            bot.send_message(
                chat_id,
                "💬 <b>История разговора пуста.</b>\n\n"
                "Поговори со мной в режиме <code>/mode chat</code>, "
                "а затем напиши <code>/report</code>.\n\n"
                "Подробнее: <code>/report help</code>",
                parse_mode="HTML",
            )
            return

        waiting_msg = bot.send_message(
            chat_id,
            "⏳ Анализирую разговор и генерирую PDF-отчёт… Это займёт несколько секунд.",
        )

        try:
            from services.report_service import generate_report

            pdf_path = generate_report(telegram_id=user_id)

            with open(pdf_path, "rb") as pdf_file:
                bot.send_document(
                    chat_id,
                    pdf_file,
                    caption=(
                        "📄 <b>Отчёт по нашему разговору готов!</b>\n\n"
                        "В PDF — тема, ключевые тезисы, решения, открытые вопросы и следующие шаги."
                    ),
                    parse_mode="HTML",
                )

            logger.info(
                "report_sent",
                extra={"event": "report_sent", "telegram_id": user_id, "path": pdf_path},
            )

        except ValueError as e:
            bot.send_message(
                chat_id,
                f"⚠️ {e}",
                parse_mode="HTML",
            )
            logger.warning("report_value_error", extra={"error": str(e), "telegram_id": user_id})

        except ImportError as e:
            bot.send_message(
                chat_id,
                "❌ <b>PDF-генерация недоступна.</b>\n\n"
                "На сервере не установлены необходимые библиотеки (<code>jinja2</code>, <code>weasyprint</code>).\n"
                "Обратитесь к администратору.",
                parse_mode="HTML",
            )
            logger.error("report_import_error", extra={"error": str(e), "telegram_id": user_id})

        except Exception as e:
            bot.send_message(
                chat_id,
                "❌ Не удалось сгенерировать отчёт. Попробуй позже.",
            )
            logger.exception(
                "report_unexpected_error",
                extra={"error": str(e), "telegram_id": user_id},
            )

        finally:
            try:
                bot.delete_message(chat_id, waiting_msg.message_id)
            except Exception:
                pass
