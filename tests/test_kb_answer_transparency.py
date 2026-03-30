from __future__ import annotations

from services import kb_answer_transparency


def test_footer_absent_when_kb_disabled():
    text, mode = kb_answer_transparency.build_kb_answer_footer(
        kb_enabled=False,
        kb_used=False,
        source_docs=[],
        results_count=0,
    )
    assert text is None
    assert mode is None


def test_footer_shows_kb_sources_when_used():
    text, mode = kb_answer_transparency.build_kb_answer_footer(
        kb_enabled=True,
        kb_used=True,
        source_docs=["NX500_rules.pdf"],
        source_refs=[],
        results_count=2,
    )
    assert mode == "HTML"
    assert "Ответ с опорой на базу знаний" in text
    assert "NX500_rules.pdf" in text
    assert "2" in text


def test_footer_explains_when_kb_not_used():
    text, mode = kb_answer_transparency.build_kb_answer_footer(
        kb_enabled=True,
        kb_used=False,
        source_docs=[],
        source_refs=[],
        results_count=0,
    )
    assert mode == "HTML"
    assert "релевантные фрагменты не найдены" in text
    assert "общим знаниям модели" in text


def test_footer_escapes_source_names():
    text, mode = kb_answer_transparency.build_kb_answer_footer(
        kb_enabled=True,
        kb_used=True,
        source_docs=["<unsafe>.pdf"],
        source_refs=[],
        results_count=1,
    )
    assert mode == "HTML"
    assert "<unsafe>.pdf" not in text
    assert "&lt;unsafe&gt;.pdf" in text


def test_footer_shows_detailed_refs_with_section_page_and_preview():
    text, mode = kb_answer_transparency.build_kb_answer_footer(
        kb_enabled=True,
        kb_used=True,
        source_docs=["NX500_rules.pdf"],
        source_refs=[
            {
                "doc_name": "NX500_rules.pdf",
                "section_title": "Съёмка с рук",
                "page_from": 12,
                "page_to": 12,
                "is_table": False,
                "block_type": "prose",
                "preview": "Используйте короткую выдержку и прижимайте локти к телу.",
            }
        ],
        results_count=3,
    )
    assert mode == "HTML"
    assert "Сноски:" in text
    assert "NX500_rules.pdf" in text
    assert "раздел: Съёмка с рук" in text
    assert "стр.: 12" in text
    assert "Используйте короткую выдержку" in text
