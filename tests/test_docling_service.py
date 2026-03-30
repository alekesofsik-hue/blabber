from __future__ import annotations

import sys
import types

import pytest

from services import docling_service


def test_parse_document_legacy_only_uses_legacy_parser(monkeypatch):
    monkeypatch.setattr(
        docling_service,
        "_parse_with_legacy",
        lambda filename, data, parser_mode: docling_service.ParsedDocument(
            filename=filename,
            text="legacy text",
            parser_backend="legacy",
            parser_mode=parser_mode,
        ),
    )

    parsed = docling_service.parse_document("demo.txt", b"hello", parser_mode="legacy_only")

    assert parsed.parser_backend == "legacy"
    assert parsed.parser_mode == "legacy_only"
    assert parsed.text == "legacy text"


def test_parse_document_docling_only_uses_docling_parser(monkeypatch):
    monkeypatch.setattr(
        docling_service,
        "_parse_with_docling",
        lambda filename, data, parser_mode: docling_service.ParsedDocument(
            filename=filename,
            text="docling text",
            parser_backend="docling",
            parser_mode=parser_mode,
        ),
    )

    parsed = docling_service.parse_document("demo.pdf", b"%PDF", parser_mode="docling_only")

    assert parsed.parser_backend == "docling"
    assert parsed.parser_mode == "docling_only"
    assert parsed.text == "docling text"


def test_parse_with_docling_routes_pdf_through_subprocess_wrapper(monkeypatch):
    monkeypatch.setattr(
        docling_service,
        "_parse_with_docling_in_subprocess",
        lambda filename, data, parser_mode: docling_service.ParsedDocument(
            filename=filename,
            text="pdf via subprocess",
            parser_backend="docling",
            parser_mode=parser_mode,
        ),
    )

    parsed = docling_service._parse_with_docling("demo.pdf", b"%PDF", parser_mode="docling_only")

    assert parsed.text == "pdf via subprocess"


def test_parse_with_docling_routes_non_pdf_through_inprocess_parser(monkeypatch):
    monkeypatch.setattr(
        docling_service,
        "_parse_with_docling_inprocess",
        lambda filename, data, parser_mode: docling_service.ParsedDocument(
            filename=filename,
            text="md via inprocess",
            parser_backend="docling",
            parser_mode=parser_mode,
        ),
    )

    parsed = docling_service._parse_with_docling("demo.md", b"# md", parser_mode="docling_only")

    assert parsed.text == "md via inprocess"


def test_parse_document_docling_with_fallback_returns_legacy_on_failure(monkeypatch):
    def _boom(filename, data, parser_mode):
        raise ValueError("docling failed")

    monkeypatch.setattr(docling_service, "_parse_with_docling", _boom)
    monkeypatch.setattr(
        docling_service,
        "_parse_with_legacy",
        lambda filename, data, parser_mode: docling_service.ParsedDocument(
            filename=filename,
            text="legacy fallback text",
            parser_backend="legacy",
            parser_mode=parser_mode,
        ),
    )

    parsed = docling_service.parse_document(
        "demo.pdf",
        b"%PDF",
        parser_mode="docling_with_legacy_fallback",
    )

    assert parsed.parser_backend == "legacy"
    assert parsed.parser_mode == "docling_with_legacy_fallback"
    assert parsed.fallback_used is True
    assert parsed.fallback_reason == "docling failed"
    assert "Docling fallback: docling failed" in parsed.warnings


def test_parse_document_docling_with_fallback_re_raises_when_policy_disallows(monkeypatch):
    monkeypatch.setattr(docling_service.kb_rollout, "should_continue_after_docling_failure", lambda: False)

    def _boom(filename, data, parser_mode):
        raise ValueError("docling hard fail")

    monkeypatch.setattr(docling_service, "_parse_with_docling", _boom)

    with pytest.raises(ValueError, match="docling hard fail"):
        docling_service.parse_document(
            "demo.pdf",
            b"%PDF",
            parser_mode="docling_with_legacy_fallback",
        )


def test_legacy_parser_supports_txt():
    parsed = docling_service._parse_with_legacy("demo.txt", "привет".encode("utf-8"), parser_mode="legacy_only")

    assert parsed.text == "привет"
    assert parsed.source_format == "txt"


def test_docling_support_matrix_marks_txt_as_unsupported():
    assert docling_service.is_docling_supported_filename("demo.txt") is False
    assert docling_service.is_docling_supported_filename("demo.md") is True
    assert docling_service.is_docling_supported_filename("demo.pdf") is True


def test_parse_document_unsupported_format_falls_back_in_hybrid_mode():
    parsed = docling_service.parse_document(
        "demo.txt",
        b"hello",
        parser_mode="docling_with_legacy_fallback",
    )

    assert parsed.parser_backend == "legacy"
    assert parsed.fallback_used is True
    assert parsed.fallback_reason == "docling_format_not_supported"
    assert parsed.metadata["docling_unsupported_format"] is True


def test_parse_document_unsupported_format_fails_in_docling_only_mode():
    with pytest.raises(ValueError, match="не поддерживает формат"):
        docling_service.parse_document(
            "demo.txt",
            b"hello",
            parser_mode="docling_only",
        )


def test_docling_parser_reports_missing_dependency(monkeypatch):
    original_import = __import__

    def _fake_import(name, *args, **kwargs):
        if name.startswith("docling"):
            raise ImportError("docling missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _fake_import)

    with pytest.raises(ValueError, match="docling"):
        docling_service._parse_with_docling_inprocess("demo.pdf", b"%PDF", parser_mode="docling_only")


def test_create_docling_converter_disables_ocr_for_pdf(monkeypatch):
    calls: dict[str, object] = {}

    fake_base_models = types.ModuleType("docling.datamodel.base_models")
    fake_base_models.InputFormat = types.SimpleNamespace(PDF="PDF")

    class FakePdfPipelineOptions:
        def __init__(self, *, do_ocr=True):
            calls["do_ocr"] = do_ocr

    fake_pipeline_options = types.ModuleType("docling.datamodel.pipeline_options")
    fake_pipeline_options.PdfPipelineOptions = FakePdfPipelineOptions

    class FakePdfFormatOption:
        def __init__(self, *, pipeline_options=None):
            calls["pipeline_options"] = pipeline_options

    class FakeDocumentConverter:
        def __init__(self, allowed_formats=None, format_options=None):
            calls["allowed_formats"] = allowed_formats
            calls["format_options"] = format_options

    fake_document_converter = types.ModuleType("docling.document_converter")
    fake_document_converter.DocumentConverter = FakeDocumentConverter
    fake_document_converter.PdfFormatOption = FakePdfFormatOption

    monkeypatch.setitem(sys.modules, "docling.datamodel.base_models", fake_base_models)
    monkeypatch.setitem(sys.modules, "docling.datamodel.pipeline_options", fake_pipeline_options)
    monkeypatch.setitem(sys.modules, "docling.document_converter", fake_document_converter)

    converter = docling_service._create_docling_converter("demo.pdf")

    assert isinstance(converter, FakeDocumentConverter)
    assert calls["do_ocr"] is False
    assert "PDF" in calls["format_options"]


def test_docling_pdf_timeout_is_adaptive(monkeypatch):
    monkeypatch.delenv("KB_DOCLING_PDF_TIMEOUT_SEC", raising=False)

    small_timeout = docling_service._get_docling_pdf_timeout_sec(512 * 1024)
    large_timeout = docling_service._get_docling_pdf_timeout_sec(8 * 1024 * 1024)

    assert small_timeout >= 180
    assert large_timeout > small_timeout
    assert large_timeout <= 420
