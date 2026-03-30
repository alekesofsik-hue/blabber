"""
User-facing transparency helpers for KB-backed answers.

Goal:
- make it obvious whether the final answer used retrieved KB fragments
- keep the main LLM answer clean
- provide lightweight provenance without exposing raw chunk text by default
"""

from __future__ import annotations

import html


def build_kb_answer_footer(
    *,
    kb_enabled: bool,
    kb_used: bool,
    source_docs: list[str] | None = None,
    source_refs: list[dict] | None = None,
    results_count: int = 0,
) -> tuple[str | None, str | None]:
    """
    Return (text, parse_mode) for a transparency footer.

    When KB is disabled entirely, returns (None, None).
    """
    if not kb_enabled:
        return None, None

    docs = [d for d in (source_docs or []) if d]
    escaped_docs = [html.escape(doc) for doc in docs[:3]]
    refs = list(source_refs or [])
    more_suffix = ""
    if len(docs) > 3:
        more_suffix = f" и ещё {len(docs) - 3}"

    if kb_used:
        docs_line = ", ".join(escaped_docs) if escaped_docs else "источник не определён"
        lines = [
            "📚 <i>Ответ с опорой на базу знаний.</i>\n"
            f"<i>Найдено фрагментов: {int(results_count)}. Источники: {docs_line}{more_suffix}.</i>"
        ]
        if refs:
            lines.append("\n<b>Сноски:</b>")
            for ref in refs[:3]:
                meta_parts: list[str] = []
                doc_name = html.escape(str(ref.get("doc_name") or "источник"))
                meta_parts.append(doc_name)

                section_title = str(ref.get("section_title") or "").strip()
                if section_title:
                    meta_parts.append(f"раздел: {html.escape(section_title)}")

                page_from = ref.get("page_from")
                page_to = ref.get("page_to")
                if page_from is not None and page_to is not None and page_from != page_to:
                    meta_parts.append(f"стр.: {int(page_from)}-{int(page_to)}")
                elif page_from is not None:
                    meta_parts.append(f"стр.: {int(page_from)}")
                elif page_to is not None:
                    meta_parts.append(f"стр.: {int(page_to)}")

                if ref.get("is_table"):
                    meta_parts.append("таблица")
                elif ref.get("block_type"):
                    meta_parts.append(html.escape(str(ref.get("block_type"))))

                lines.append("• " + " · ".join(meta_parts))

                preview = str(ref.get("preview") or "").strip()
                if preview:
                    lines.append(f"<i>«{html.escape(preview)}»</i>")

            if int(results_count) > len(refs[:3]):
                lines.append(f"<i>Показаны основные сноски; всего найдено фрагментов: {int(results_count)}.</i>")

        return "\n".join(lines), "HTML"

    text = (
        "📚 <i>База знаний включена, но по этому вопросу релевантные фрагменты не найдены.</i>\n"
        "<i>Ответ мог быть дан по общим знаниям модели.</i>"
    )
    return text, "HTML"
