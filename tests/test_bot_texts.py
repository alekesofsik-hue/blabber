"""Тесты встроенных шаблонов /start и /help."""

from bot_texts.defaults import (
    HELP_MESSAGE_HTML,
    resolve_help_message,
    resolve_start_message,
)


def test_resolve_start_builtin_html():
    text, mode = resolve_start_message("openrouter", None)
    assert mode == "HTML"
    assert "<b>Blabber</b>" in text
    assert "openrouter" in text


def test_resolve_start_escapes_model_in_html():
    text, mode = resolve_start_message("<script>", None)
    assert mode == "HTML"
    assert "<script>" not in text
    assert "&lt;script&gt;" in text


def test_resolve_start_override_plain():
    text, mode = resolve_start_message("m", "Привет, {model}!")
    assert mode is None
    assert text == "Привет, m!"


def test_resolve_start_override_empty_uses_builtin():
    text, mode = resolve_start_message("x", "   ")
    assert mode == "HTML"
    assert "Blabber" in text


def test_resolve_help_builtin():
    text, mode = resolve_help_message(None)
    assert mode == "HTML"
    assert text == HELP_MESSAGE_HTML


def test_resolve_help_override():
    text, mode = resolve_help_message("Кастомная справка")
    assert mode is None
    assert text == "Кастомная справка"
