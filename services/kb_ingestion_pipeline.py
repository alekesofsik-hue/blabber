"""
Structured KB ingestion helpers for Docling-powered uploads.

Sprint 3 goal:
- build a canonical normalized representation of a parsed document
- extract coarse structured blocks from Docling markdown/text
- build chunk payloads with metadata suitable for SQLite + LanceDB persistence
- keep the implementation storage-agnostic so knowledge_service can orchestrate
  rollout flags, embeddings, and persistence
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


@dataclass
class NormalizedBlock:
    text: str
    block_type: str
    section_title: str | None = None
    heading_path: list[str] = field(default_factory=list)
    page_from: int | None = None
    page_to: int | None = None
    is_table: bool = False
    table_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedDocument:
    filename: str
    text: str
    parser_backend: str
    source_format: str | None = None
    blocks: list[NormalizedBlock] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkPayload:
    text: str
    section_title: str | None = None
    heading_path: list[str] = field(default_factory=list)
    page_from: int | None = None
    page_to: int | None = None
    block_type: str = "text"
    is_table: bool = False
    table_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def _heading_match(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def _looks_like_table_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return stripped.count("|") >= 2


def _looks_like_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    normalized = stripped.replace("|", "").replace(":", "").replace("-", "").replace(" ", "")
    return normalized == ""


def _split_text_with_overlap(
    text: str,
    *,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            for sep in ("\n\n", ".\n", ". ", "\n", " "):
                pos = text.rfind(sep, start + overlap, end)
                if pos > start:
                    end = pos + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        next_start = end - overlap
        start = max(next_start, start + 1)

    return chunks


def _emit_prose_block(
    blocks: list[NormalizedBlock],
    buffer: list[str],
    heading_path: list[str],
    *,
    fallback_section_title: str | None,
) -> None:
    text = "\n".join(line.rstrip() for line in buffer).strip()
    if not text:
        return
    blocks.append(
        NormalizedBlock(
            text=text,
            block_type="prose",
            section_title=(heading_path[-1] if heading_path else fallback_section_title),
            heading_path=list(heading_path),
        )
    )


def extract_structured_blocks(text: str, *, fallback_headings: list[str] | None = None) -> list[NormalizedBlock]:
    """
    Best-effort conversion from Docling markdown/text into structured blocks.

    This does not try to mirror the full Docling AST; it builds a stable local
    representation that keeps section boundaries and tables separate for chunking.
    """
    lines = text.splitlines()
    blocks: list[NormalizedBlock] = []
    heading_path: list[str] = []
    prose_buffer: list[str] = []
    fallback_section_title = (fallback_headings or [None])[0]
    table_counter = 0

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        heading = _heading_match(line)
        if heading:
            _emit_prose_block(
                blocks,
                prose_buffer,
                heading_path,
                fallback_section_title=fallback_section_title,
            )
            prose_buffer = []
            level, title = heading
            heading_path = heading_path[: level - 1]
            heading_path.append(title)
            idx += 1
            continue

        if not stripped:
            _emit_prose_block(
                blocks,
                prose_buffer,
                heading_path,
                fallback_section_title=fallback_section_title,
            )
            prose_buffer = []
            idx += 1
            continue

        if _looks_like_table_line(line):
            next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
            if _looks_like_table_separator(next_line) or (
                idx > 0 and _looks_like_table_line(lines[idx - 1])
            ):
                _emit_prose_block(
                    blocks,
                    prose_buffer,
                    heading_path,
                    fallback_section_title=fallback_section_title,
                )
                prose_buffer = []

                table_lines = [line.rstrip()]
                idx += 1
                while idx < len(lines):
                    table_line = lines[idx]
                    if not table_line.strip():
                        break
                    if not (_looks_like_table_line(table_line) or _looks_like_table_separator(table_line)):
                        break
                    table_lines.append(table_line.rstrip())
                    idx += 1

                table_counter += 1
                blocks.append(
                    NormalizedBlock(
                        text="\n".join(table_lines).strip(),
                        block_type="table",
                        section_title=(heading_path[-1] if heading_path else fallback_section_title),
                        heading_path=list(heading_path),
                        is_table=True,
                        table_id=f"table_{table_counter}",
                    )
                )
                continue

        prose_buffer.append(line.rstrip())
        idx += 1

    _emit_prose_block(
        blocks,
        prose_buffer,
        heading_path,
        fallback_section_title=fallback_section_title,
    )

    if blocks:
        return blocks

    text = text.strip()
    if not text:
        return []
    return [
        NormalizedBlock(
            text=text,
            block_type="text",
            section_title=fallback_section_title,
            heading_path=[fallback_section_title] if fallback_section_title else [],
        )
    ]


def normalize_document(
    *,
    filename: str,
    text: str,
    parser_backend: str,
    source_format: str | None = None,
    structure: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> NormalizedDocument:
    headings = []
    if isinstance(structure, dict):
        headings = list(structure.get("headings") or [])
        raw_blocks = structure.get("blocks")
        if isinstance(raw_blocks, list) and raw_blocks:
            blocks = [
                NormalizedBlock(
                    text=str(block.get("text", "")).strip(),
                    block_type=str(block.get("block_type", "text")),
                    section_title=block.get("section_title"),
                    heading_path=list(block.get("heading_path") or []),
                    page_from=block.get("page_from"),
                    page_to=block.get("page_to"),
                    is_table=bool(block.get("is_table")),
                    table_id=block.get("table_id"),
                    meta=dict(block.get("meta") or {}),
                )
                for block in raw_blocks
                if str(block.get("text", "")).strip()
            ]
        else:
            blocks = extract_structured_blocks(text, fallback_headings=headings)
    else:
        blocks = extract_structured_blocks(text)

    return NormalizedDocument(
        filename=filename,
        text=text,
        parser_backend=parser_backend,
        source_format=source_format,
        blocks=blocks,
        metadata=dict(metadata or {}),
    )


def _render_heading_prefix(heading_path: list[str], *, is_table: bool) -> str:
    if not heading_path:
        return "[Таблица]\n\n" if is_table else ""
    label = " > ".join(heading_path)
    if is_table:
        return f"[Таблица | Раздел: {label}]\n\n"
    return f"[Раздел: {label}]\n\n"


def _build_prose_chunks(
    block: NormalizedBlock,
    *,
    chunk_size: int,
    overlap: int,
) -> list[ChunkPayload]:
    base_prefix = _render_heading_prefix(block.heading_path, is_table=False)
    available_size = max(200, chunk_size - len(base_prefix))
    raw_chunks = _split_text_with_overlap(
        block.text,
        chunk_size=available_size,
        overlap=min(overlap, max(0, available_size // 3)),
    )
    return [
        ChunkPayload(
            text=f"{base_prefix}{chunk}".strip(),
            section_title=block.section_title,
            heading_path=list(block.heading_path),
            page_from=block.page_from,
            page_to=block.page_to,
            block_type=block.block_type,
            is_table=False,
            table_id=None,
            meta=dict(block.meta),
        )
        for chunk in raw_chunks
        if chunk.strip()
    ]


def _build_table_chunks(
    block: NormalizedBlock,
    *,
    chunk_size: int,
) -> list[ChunkPayload]:
    prefix = _render_heading_prefix(block.heading_path, is_table=True)
    lines = [line for line in block.text.splitlines() if line.strip()]
    if not lines:
        return []

    if len(lines) <= 3:
        rendered = f"{prefix}{block.text}".strip()
        return [
            ChunkPayload(
                text=rendered,
                section_title=block.section_title,
                heading_path=list(block.heading_path),
                page_from=block.page_from,
                page_to=block.page_to,
                block_type="table",
                is_table=True,
                table_id=block.table_id,
                meta=dict(block.meta),
            )
        ]

    header = lines[:2]
    data_rows = lines[2:]
    table_chunks: list[ChunkPayload] = []
    current_rows: list[str] = []

    for row in data_rows:
        candidate_rows = current_rows + [row]
        candidate_text = "\n".join([*header, *candidate_rows]).strip()
        rendered = f"{prefix}{candidate_text}".strip()
        if current_rows and len(rendered) > chunk_size:
            final_text = f"{prefix}{'\n'.join([*header, *current_rows]).strip()}".strip()
            table_chunks.append(
                ChunkPayload(
                    text=final_text,
                    section_title=block.section_title,
                    heading_path=list(block.heading_path),
                    page_from=block.page_from,
                    page_to=block.page_to,
                    block_type="table",
                    is_table=True,
                    table_id=block.table_id,
                    meta=dict(block.meta),
                )
            )
            current_rows = [row]
        else:
            current_rows = candidate_rows

    if current_rows:
        final_text = f"{prefix}{'\n'.join([*header, *current_rows]).strip()}".strip()
        table_chunks.append(
            ChunkPayload(
                text=final_text,
                section_title=block.section_title,
                heading_path=list(block.heading_path),
                page_from=block.page_from,
                page_to=block.page_to,
                block_type="table",
                is_table=True,
                table_id=block.table_id,
                meta=dict(block.meta),
            )
        )

    return table_chunks


def build_chunks(
    document: NormalizedDocument,
    *,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[ChunkPayload]:
    chunks: list[ChunkPayload] = []
    for block in document.blocks:
        if block.is_table or block.block_type == "table":
            chunks.extend(_build_table_chunks(block, chunk_size=chunk_size))
        else:
            chunks.extend(_build_prose_chunks(block, chunk_size=chunk_size, overlap=overlap))

    for chunk in chunks:
        chunk.meta = {
            "parser_backend": document.parser_backend,
            "source_format": document.source_format,
            **chunk.meta,
            "char_count": len(chunk.text),
            "token_estimate": max(1, len(chunk.text) // 4),
        }
    return [chunk for chunk in chunks if chunk.text.strip()]


def summarize_document_structure(document: NormalizedDocument, chunks: list[ChunkPayload]) -> dict[str, Any]:
    return {
        "block_count": len(document.blocks),
        "chunk_count": len(chunks),
        "table_count": sum(1 for block in document.blocks if block.is_table or block.block_type == "table"),
        "section_count": len({tuple(block.heading_path) for block in document.blocks if block.heading_path}),
    }
