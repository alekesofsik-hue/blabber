"""
Knowledge service — long-term memory C (RAG).

Pipeline:
  Upload → extract text → chunk → compute embeddings → store in SQLite + LanceDB
  Query  → BM25 shortlist + LanceDB semantic candidates → merged rerank → inject top-K into LLM context

Hybrid retrieval strategy:
  1. BM25 — lexical shortlist (cheap, keyword match) → top BM25_SHORTLIST_K
  2. LanceDB vector search — semantic candidates from the shared vector store
  3. Final score = α * norm(BM25) + (1-α) * norm(semantic)

Graceful degradation: if embeddings are unavailable (no API key, API error)
the system falls back to BM25-only retrieval — quality degrades but nothing breaks.

Supports TXT, PDF, DOC, DOCX, MD and URL ingestion.
Primary parser is Docling with rollout flags and legacy fallback where needed.

Legacy note:
- `kb_chunks.embedding` is now optional and disabled by default for new writes.
- It can still be refreshed intentionally as a rollback buffer for `KB_VECTOR_BACKEND=sqlite`.
- The primary read path is now `LanceDB` (`KB_VECTOR_BACKEND=lancedb` by default).
"""

from __future__ import annotations

from dataclasses import asdict
import json
import logging
import math
import os
import re
from collections import Counter
from typing import Any

import repositories.knowledge_repo as kb_repo
import repositories.kb_vector_repo as kb_vector_repo
from database import get_connection
from repositories.user_repo import get_by_telegram_id
import services.context_service as ctx_svc
import services.document_summary_service as doc_summary_svc
import services.docling_service as docling_svc
import services.kb_ingestion_pipeline as kb_ingest_svc
import services.kb_upload_feedback as kb_feedback_svc
from services import embedding_service as emb_svc
from services import kb_rollout
from services import url_ingestion_service as url_ing_svc
from services.config_registry import get_setting

logger = logging.getLogger("blabber")

# ── Tunables ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 800           # characters per chunk (up from 500 for better embedding context)
CHUNK_OVERLAP: int = 100        # overlap between consecutive chunks
MAX_DOCS_PER_USER: int = 10
DEFAULT_MAX_DOC_SIZE_KB: int = 3072   # 3 MiB
RETRIEVAL_TOP_K: int = 3
RETRIEVAL_MAX_CHARS: int = 1_500      # total chars injected into LLM context
BM25_SHORTLIST_K: int = 10            # how many BM25 candidates to pass to reranker
HYBRID_ALPHA: float = 0.3            # weight for BM25 in final score (0.3 BM25, 0.7 embedding)
STRUCTURED_SECTION_BOOST: float = 0.12
STRUCTURED_TABLE_BOOST: float = 0.18
STRUCTURED_PAGE_BOOST: float = 0.08
TABLE_CONTEXT_MAX_CHARS: int = 420


def _uid(telegram_id: int) -> int | None:
    user = get_by_telegram_id(telegram_id)
    return user["id"] if user else None


def get_max_doc_size_bytes() -> int:
    """
    Configurable KB upload limit in bytes.

    Stored in config as KiB so admins can change it from /admin without dealing
    with large raw byte values.
    """
    raw = get_setting("kb_max_doc_size_kb", DEFAULT_MAX_DOC_SIZE_KB)
    try:
        kib = int(raw)
    except (TypeError, ValueError):
        kib = DEFAULT_MAX_DOC_SIZE_KB
    return max(1, kib) * 1024


def format_doc_size_limit(limit_bytes: int | None = None) -> str:
    """Human-readable KB upload limit for Telegram messages."""
    size_bytes = int(limit_bytes or get_max_doc_size_bytes())
    mib = size_bytes / (1024 * 1024)
    if size_bytes % (1024 * 1024) == 0:
        return f"{int(mib)} МБ"
    if mib >= 1:
        return f"{mib:.1f} МБ"
    return f"{max(1, size_bytes // 1024)} КБ"


def _is_dual_write_enabled() -> bool:
    """
    True if KB dual-write to LanceDB is enabled.

    The primary read path is LanceDB, so by default we still write vectors to
    the shared vector store during indexing and reindex operations.
    """
    raw = os.getenv("KB_ENABLE_DUAL_WRITE", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _is_legacy_embedding_write_enabled() -> bool:
    """
    True if we still persist legacy embedding BLOBs into kb_chunks.embedding.

    Post-cutover default: disabled. The field remains only as an optional
    rollback buffer for operators who explicitly enable it and run reindex.
    """
    raw = os.getenv("KB_WRITE_LEGACY_EMBEDDING", "false").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _get_vector_backend() -> str:
    """
    Return the active KB retrieval backend.

    Supported values:
    - sqlite: legacy retrieval via embedding BLOB in kb_chunks
    - lancedb: new retrieval via kb_vector_repo + SQLite enrichment
    - hybrid_migration: return new retrieval, but also compare against legacy
    """
    raw = os.getenv("KB_VECTOR_BACKEND", "lancedb").strip().lower()
    if raw in {"sqlite", "lancedb", "hybrid_migration"}:
        return raw
    return "lancedb"


def _is_shadow_compare_enabled() -> bool:
    """
    True if automatic shadow compare is enabled on top of the default lancedb
    read path.
    """
    raw = os.getenv("KB_ENABLE_SHADOW_COMPARE", "false").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def is_url_ingestion_enabled() -> bool:
    """True if URL ingestion into KB is enabled."""
    raw = os.getenv("KB_ENABLE_URL_INGESTION", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _build_vector_rows(
    *,
    chunk_uids: list[str],
    chunks: list[str],
    vectors: list[list[float]] | None,
) -> list[dict[str, Any]]:
    """Build KB vector rows aligned by chunk index."""
    if not vectors or len(vectors) != len(chunks) or len(chunk_uids) != len(chunks):
        return []

    return [
        {
            "chunk_uid": chunk_uid,
            "chunk_idx": idx,
            "content": text,
            "vector": vector,
        }
        for idx, (chunk_uid, text, vector) in enumerate(zip(chunk_uids, chunks, vectors))
    ]


def _build_document_store_payload(
    parsed: docling_svc.ParsedDocument | None,
    *,
    ingestion_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if parsed is None:
        return {}
    return {
        "parser_backend": parsed.parser_backend,
        "parser_mode": parsed.parser_mode,
        "parser_version": parsed.parser_version,
        "source_format": parsed.source_format,
        "doc_structure": parsed.structure or {},
        "doc_metadata": {
            **(parsed.metadata or {}),
            "warnings": list(parsed.warnings or []),
            "fallback_used": bool(parsed.fallback_used),
            "fallback_reason": parsed.fallback_reason,
            **(ingestion_stats or {}),
        },
        "doc_has_tables": bool(parsed.has_tables),
        "doc_has_headings": bool(parsed.has_headings),
        "doc_page_count": parsed.page_count,
        "summary_status": "pending",
    }


def _document_metadata_richness(doc: dict[str, Any], chunks: list[dict[str, Any]] | None = None) -> str:
    score = 0
    if doc.get("parser_backend"):
        score += 1
    if doc.get("doc_has_tables"):
        score += 1
    if doc.get("doc_has_headings"):
        score += 1
    if doc.get("summary_status") in {"generated", "fallback_preview"}:
        score += 1
    if chunks and any(chunk.get("section_title") or chunk.get("is_table") for chunk in chunks):
        score += 1
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _reconstruct_parsed_document_from_storage(
    doc: dict[str, Any],
    chunks: list[dict[str, Any]],
) -> docling_svc.ParsedDocument:
    ordered_chunks = sorted(chunks, key=lambda row: row.get("chunk_idx", 0))
    text = "\n\n".join((row.get("content") or "").strip() for row in ordered_chunks if (row.get("content") or "").strip())
    headings: list[str] = []
    for row in ordered_chunks:
        for heading in row.get("heading_path_json") or []:
            if heading and heading not in headings:
                headings.append(str(heading))

    doc_metadata = dict(doc.get("doc_metadata_json") or {})
    warnings = list(doc_metadata.get("warnings") or [])
    return docling_svc.ParsedDocument(
        filename=doc["name"],
        text=text,
        parser_backend=doc.get("parser_backend") or "legacy",
        parser_mode=doc.get("parser_mode") or "legacy_only",
        parser_version=doc.get("parser_version"),
        source_format=doc.get("source_format"),
        page_count=doc.get("doc_page_count"),
        has_tables=bool(doc.get("doc_has_tables")),
        has_headings=bool(doc.get("doc_has_headings")),
        structure=doc.get("doc_structure_json") or {"headings": headings},
        warnings=warnings,
        fallback_used=bool(doc_metadata.get("fallback_used")),
        fallback_reason=doc_metadata.get("fallback_reason"),
        metadata={k: v for k, v in doc_metadata.items() if k != "warnings"},
    )


def _backfill_structured_metadata_from_chunks(
    *,
    user_db_id: int,
    doc: dict[str, Any],
    chunks: list[dict[str, Any]],
    dry_run: bool = False,
) -> dict[str, Any]:
    chunk_texts = [row["content"] for row in chunks]
    rebuilt_chunk_meta = _build_chunk_metadata(
        chunk_texts,
        parsed=_reconstruct_parsed_document_from_storage(doc, chunks),
    )
    rebuilt_chunk_map = {
        row["chunk_uid"]: meta
        for row, meta in zip(chunks, rebuilt_chunk_meta)
        if row.get("chunk_uid")
    }
    headings: list[str] = []
    for meta in rebuilt_chunk_meta:
        for heading in meta.get("heading_path") or []:
            if heading and heading not in headings:
                headings.append(str(heading))

    updates = {
        "doc_has_tables": any(bool(meta.get("is_table")) for meta in rebuilt_chunk_meta),
        "doc_has_headings": any(bool(meta.get("heading_path")) for meta in rebuilt_chunk_meta),
        "doc_page_count": max(
            [page for meta in rebuilt_chunk_meta for page in (meta.get("page_from"), meta.get("page_to")) if page is not None] or [doc.get("doc_page_count")]
        ),
        "doc_structure": {"headings": headings[:50]},
        "doc_metadata": {
            **(doc.get("doc_metadata_json") or {}),
            "structured_backfill_applied": True,
        },
        "chunk_updates": len(rebuilt_chunk_map),
    }
    if not dry_run:
        kb_repo.update_document_structured_fields(
            doc["id"],
            user_db_id,
            parser_backend=doc.get("parser_backend") or "legacy",
            parser_mode=doc.get("parser_mode") or "legacy_only",
            parser_version=doc.get("parser_version"),
            source_format=doc.get("source_format"),
            doc_structure=updates["doc_structure"],
            doc_metadata=updates["doc_metadata"],
            doc_has_tables=updates["doc_has_tables"],
            doc_has_headings=updates["doc_has_headings"],
            doc_page_count=updates["doc_page_count"],
        )
        kb_repo.update_chunk_structured_metadata(
            user_db_id,
            [(chunk_uid, meta) for chunk_uid, meta in rebuilt_chunk_map.items()],
        )
    return updates


def _regenerate_document_summary_from_storage(
    *,
    telegram_id: int,
    user_db_id: int,
    doc: dict[str, Any],
    chunks: list[dict[str, Any]],
    dry_run: bool = False,
) -> dict[str, Any]:
    parsed = _reconstruct_parsed_document_from_storage(doc, chunks)
    artifacts = doc_summary_svc.generate_summary_artifacts(
        telegram_id,
        filename=doc["name"],
        parsed_document=parsed,
    )
    if not dry_run:
        kb_repo.update_document_summary(
            doc["id"],
            user_db_id,
            summary_text=artifacts.summary or None,
            summary_topics=artifacts.key_topics,
            summary_questions=artifacts.suggested_questions,
            summary_status=artifacts.status,
            summary_generated_at=artifacts.generated_at,
            summary_error=artifacts.error,
        )
    return asdict(artifacts)


def _build_chunk_metadata(
    chunks: list[str],
    *,
    parsed: docling_svc.ParsedDocument | None,
) -> list[dict[str, Any]]:
    """
    Prepare chunk-level structured metadata for SQLite storage.

    Sprint 2 keeps this intentionally lightweight: it stores stable defaults and
    a best-effort section/table signal so later sprints can enrich the pipeline
    without changing storage contracts again.
    """
    parser_backend = parsed.parser_backend if parsed else "legacy"
    source_format = parsed.source_format if parsed else None
    headings = []
    if parsed and isinstance(parsed.structure, dict):
        headings = list(parsed.structure.get("headings") or [])

    result: list[dict[str, Any]] = []
    for chunk in chunks:
        section_title = None
        for line in chunk.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                section_title = stripped.lstrip("#").strip() or None
                break
        if section_title is None and headings:
            section_title = headings[0]
        is_table = any(line.strip().count("|") >= 2 for line in chunk.splitlines())
        result.append(
            {
                "section_title": section_title,
                "heading_path": [section_title] if section_title else None,
                "page_from": None,
                "page_to": None,
                "block_type": "table" if is_table else ("markdown" if parser_backend == "docling" else "text"),
                "is_table": is_table,
                "table_id": None,
                "meta": {
                    "parser_backend": parser_backend,
                    "source_format": source_format,
                    "char_count": len(chunk),
                },
            }
        )
    return result


def _chunk_payloads_to_repo_metadata(
    chunk_payloads: list[kb_ingest_svc.ChunkPayload],
) -> list[dict[str, Any]]:
    return [
        {
            "section_title": chunk.section_title,
            "heading_path": list(chunk.heading_path) if chunk.heading_path else None,
            "page_from": chunk.page_from,
            "page_to": chunk.page_to,
            "block_type": chunk.block_type,
            "is_table": chunk.is_table,
            "table_id": chunk.table_id,
            "meta": dict(chunk.meta),
        }
        for chunk in chunk_payloads
    ]


def _build_ingestion_chunks(
    *,
    name: str,
    text: str,
    parsed_document: docling_svc.ParsedDocument | None,
) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    use_structured = bool(
        parsed_document
        and parsed_document.parser_backend == "docling"
        and kb_rollout.is_docling_structured_chunks_enabled()
    )

    if use_structured:
        try:
            normalized = kb_ingest_svc.normalize_document(
                filename=name,
                text=text,
                parser_backend=parsed_document.parser_backend,
                source_format=parsed_document.source_format,
                structure=parsed_document.structure,
                metadata=parsed_document.metadata,
            )
            chunk_payloads = kb_ingest_svc.build_chunks(
                normalized,
                chunk_size=CHUNK_SIZE,
                overlap=CHUNK_OVERLAP,
            )
            if chunk_payloads:
                structure_stats = kb_ingest_svc.summarize_document_structure(normalized, chunk_payloads)
                return (
                    [chunk.text for chunk in chunk_payloads],
                    _chunk_payloads_to_repo_metadata(chunk_payloads),
                    {
                        "pipeline_mode": "structured_docling",
                        "normalized_block_count": structure_stats["block_count"],
                        "table_count": structure_stats["table_count"],
                        "section_count": structure_stats["section_count"],
                        "chunking_fallback_used": False,
                    },
                )
            fallback_reason = "structured_chunk_builder_returned_empty"
        except Exception as exc:
            logger.warning(
                "kb_structured_chunk_build_failed",
                extra={
                    "event": "kb_structured_chunk_build_failed",
                    "doc_name": name,
                    "error": str(exc)[:200],
                },
            )
            fallback_reason = str(exc)[:200]
    else:
        fallback_reason = None

    legacy_chunks = chunk_text(text)
    return (
        legacy_chunks,
        _build_chunk_metadata(legacy_chunks, parsed=parsed_document),
        {
            "pipeline_mode": "legacy_chunk_text",
            "normalized_block_count": 0,
            "table_count": int(bool(getattr(parsed_document, "has_tables", False))),
            "section_count": len(list((getattr(parsed_document, "structure", {}) or {}).get("headings") or [])),
            "chunking_fallback_used": bool(use_structured),
            "chunking_fallback_reason": fallback_reason,
        },
    )


def _maybe_generate_and_store_summary(
    *,
    telegram_id: int,
    user_db_id: int,
    doc_id: int,
    filename: str,
    parsed_document: docling_svc.ParsedDocument | None,
) -> doc_summary_svc.SummaryArtifacts | None:
    if parsed_document is None:
        return None
    if not kb_rollout.is_doc_summary_enabled():
        return None

    artifacts = doc_summary_svc.generate_summary_artifacts(
        telegram_id,
        filename=filename,
        parsed_document=parsed_document,
    )
    if kb_rollout.is_doc_summary_save_enabled():
        kb_repo.update_document_summary(
            doc_id,
            user_db_id,
            summary_text=artifacts.summary or None,
            summary_topics=artifacts.key_topics,
            summary_questions=artifacts.suggested_questions,
            summary_status=artifacts.status,
            summary_generated_at=artifacts.generated_at,
            summary_error=artifacts.error,
        )
    return artifacts


def _compute_embeddings_for_chunks(
    chunks: list[str],
) -> tuple[list[list[float]] | None, list[bytes | None] | None, str]:
    """
    Compute semantic vectors for KB chunks and optionally serialize legacy BLOBs.
    """
    if not emb_svc.is_available():
        return None, None, "unavailable"

    vectors = emb_svc.embed_texts(chunks)
    if not vectors or len(vectors) != len(chunks):
        logger.warning("kb_embeddings_partial_fail", extra={"chunks": len(chunks)})
        return None, None, "failed"

    embedding_blobs: list[bytes | None] | None = None
    if _is_legacy_embedding_write_enabled():
        embedding_blobs = emb_svc.vectors_to_blobs(vectors)

    logger.info(
        "kb_embeddings_computed",
        extra={
            "chunks": len(chunks),
            "legacy_blob_written": bool(embedding_blobs),
        },
    )
    return vectors, embedding_blobs, "ok"


def _normalize_similarity_from_distance(distances: list[float]) -> list[float]:
    """
    Convert LanceDB distances into normalized similarity-like scores.

    Smaller distance means better match, so we invert through 1 / (1 + d) and
    then min-max normalize to keep the scale comparable to normalized BM25.
    """
    raw = [1.0 / (1.0 + max(0.0, float(d))) for d in distances]
    return _normalize_scores(raw)


def _strip_internal_fields(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove internal helper fields from retrieval results."""
    return [
        {
            "content": row["content"],
            "doc_name": row["doc_name"],
            "score": row["score"],
            "section_title": row.get("section_title"),
            "heading_path": row.get("heading_path_json"),
            "page_from": row.get("page_from"),
            "page_to": row.get("page_to"),
            "is_table": row.get("is_table"),
            "block_type": row.get("block_type"),
        }
        for row in results
    ]


def _compute_bm25_shortlist(
    chunks: list[dict[str, Any]],
    query_tokens: list[str],
) -> list[tuple[float, int]]:
    """Compute BM25 shortlist against all KB chunks."""
    if not query_tokens:
        return []

    tokenized = [_tokenize(c["content"]) for c in chunks]
    avgdl = sum(len(t) for t in tokenized) / len(tokenized)

    bm25_scored: list[tuple[float, int]] = []
    for i, tokens in enumerate(tokenized):
        score = _bm25_score(query_tokens, tokens, avgdl)
        if score > 0:
            bm25_scored.append((score, i))

    bm25_scored.sort(key=lambda x: x[0], reverse=True)
    return bm25_scored[:BM25_SHORTLIST_K]


def _compute_structured_metadata_shortlist(
    chunks: list[dict[str, Any]],
    query: str,
    query_tokens: list[str],
) -> list[tuple[float, int]]:
    if not kb_rollout.is_structured_retrieval_enabled():
        return []

    wants_table = _is_table_friendly_query(query, query_tokens)
    wants_page = _is_page_friendly_query(query_tokens)
    scored: list[tuple[float, int]] = []
    for idx, chunk in enumerate(chunks):
        score = 0.0
        section_overlap = max(
            _overlap_ratio(query_tokens, chunk.get("section_title")),
            _overlap_ratio(query_tokens, " ".join(chunk.get("heading_path_json") or [])),
        )
        score += section_overlap
        if chunk.get("is_table") and wants_table:
            score += 0.8
        if wants_page and (chunk.get("page_from") is not None or chunk.get("page_to") is not None):
            score += 0.4
        if score > 0:
            scored.append((score, idx))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:BM25_SHORTLIST_K]


def _legacy_retrieve_context_from_chunks(
    chunks: list[dict[str, Any]],
    query: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Legacy hybrid retrieval: BM25 shortlist -> embedding BLOB rerank.

    Returns internal rows including chunk_uid for migration-time comparison.
    """
    query_tokens = _tokenize(query)
    shortlist = _compute_bm25_shortlist(chunks, query_tokens)
    metadata_shortlist = _compute_structured_metadata_shortlist(chunks, query, query_tokens)
    if not shortlist and metadata_shortlist:
        shortlist = metadata_shortlist
    if not shortlist:
        return []

    has_embeddings = any(chunks[idx].get("embedding") for _, idx in shortlist)
    if has_embeddings and emb_svc.is_available():
        query_vec = emb_svc.embed_single(query)
        if query_vec:
            bm25_raw = [s for s, _ in shortlist]
            bm25_norm = _normalize_scores(bm25_raw)

            hybrid_scored: list[dict[str, Any]] = []
            for (bm25_s_raw, idx), bm25_n in zip(shortlist, bm25_norm):
                emb_blob = chunks[idx].get("embedding")
                if emb_blob:
                    chunk_vec = emb_svc.blob_to_vector(emb_blob)
                    cos_sim = emb_svc.cosine_similarity(query_vec, chunk_vec)
                    final = HYBRID_ALPHA * bm25_n + (1 - HYBRID_ALPHA) * cos_sim
                else:
                    final = bm25_n
                hybrid_scored.append(
                    {
                        "chunk_uid": chunks[idx].get("chunk_uid"),
                        "content": chunks[idx]["content"],
                        "doc_name": chunks[idx]["doc_name"],
                        "section_title": chunks[idx].get("section_title"),
                        "heading_path_json": chunks[idx].get("heading_path_json"),
                        "page_from": chunks[idx].get("page_from"),
                        "page_to": chunks[idx].get("page_to"),
                        "is_table": chunks[idx].get("is_table"),
                        "block_type": chunks[idx].get("block_type"),
                        "score": final,
                    }
                )

            hybrid_scored = _apply_structured_retrieval_boosts(rows=hybrid_scored, query=query)
            return hybrid_scored[:top_k]

    fallback_rows = [
        {
            "chunk_uid": chunks[idx].get("chunk_uid"),
            "content": chunks[idx]["content"],
            "doc_name": chunks[idx]["doc_name"],
            "section_title": chunks[idx].get("section_title"),
            "heading_path_json": chunks[idx].get("heading_path_json"),
            "page_from": chunks[idx].get("page_from"),
            "page_to": chunks[idx].get("page_to"),
            "is_table": chunks[idx].get("is_table"),
            "block_type": chunks[idx].get("block_type"),
            "score": score,
        }
        for score, idx in shortlist[:top_k]
    ]
    fallback_rows = _apply_structured_retrieval_boosts(rows=fallback_rows, query=query)
    return fallback_rows[:top_k]


def _lancedb_retrieve_context(
    *,
    telegram_id: int,
    user_db_id: int,
    chunks: list[dict[str, Any]],
    query: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """
    New hybrid retrieval:
    1. BM25 shortlist from SQLite text
    2. semantic candidates from LanceDB
    3. merge and rerank in service layer
    """
    query_tokens = _tokenize(query)
    shortlist = _compute_bm25_shortlist(chunks, query_tokens)
    metadata_shortlist = _compute_structured_metadata_shortlist(chunks, query, query_tokens)

    bm25_score_by_uid: dict[str, float] = {}
    if shortlist:
        bm25_raw = [score for score, _ in shortlist]
        bm25_norm = _normalize_scores(bm25_raw)
        for (_, idx), score in zip(shortlist, bm25_norm):
            chunk_uid = chunks[idx].get("chunk_uid")
            if chunk_uid:
                bm25_score_by_uid[chunk_uid] = score
    for raw_score, idx in metadata_shortlist:
        chunk_uid = chunks[idx].get("chunk_uid")
        if chunk_uid:
            bm25_score_by_uid[chunk_uid] = max(bm25_score_by_uid.get(chunk_uid, 0.0), min(1.0, raw_score))

    if not emb_svc.is_available():
        logger.info(
            "kb_retrieval_fallback_bm25",
            extra={
                "event": "kb_retrieval_fallback_bm25",
                "telegram_id": telegram_id,
                "reason": "embeddings_unavailable",
            },
        )
        return _legacy_retrieve_context_from_chunks(chunks, query, top_k)

    query_vec = emb_svc.embed_single(query)
    if not query_vec:
        logger.info(
            "kb_retrieval_fallback_bm25",
            extra={
                "event": "kb_retrieval_fallback_bm25",
                "telegram_id": telegram_id,
                "reason": "query_embedding_missing",
            },
        )
        return _legacy_retrieve_context_from_chunks(chunks, query, top_k)

    try:
        semantic_results = kb_vector_repo.search_by_vector(
            user_db_id=user_db_id,
            query_vector=query_vec,
            top_k=max(BM25_SHORTLIST_K, top_k),
        )
    except Exception as exc:
        logger.warning(
            "kb_retrieval_lancedb_failed",
            extra={
                "event": "kb_retrieval_lancedb_failed",
                "telegram_id": telegram_id,
                "error": str(exc)[:200],
            },
        )
        return _legacy_retrieve_context_from_chunks(chunks, query, top_k)

    if not semantic_results and not shortlist and not metadata_shortlist:
        return []
    if not semantic_results and not bm25_score_by_uid:
        logger.info(
            "kb_retrieval_fallback_bm25",
            extra={
                "event": "kb_retrieval_fallback_bm25",
                "telegram_id": telegram_id,
                "reason": "empty_vector_results",
            },
        )
        return _legacy_retrieve_context_from_chunks(chunks, query, top_k)

    semantic_norm = _normalize_similarity_from_distance([row["distance"] for row in semantic_results])
    semantic_score_by_uid = {
        row["chunk_uid"]: score
        for row, score in zip(semantic_results, semantic_norm)
        if row.get("chunk_uid")
    }

    candidate_uids = list(dict.fromkeys([
        *bm25_score_by_uid.keys(),
        *semantic_score_by_uid.keys(),
    ]))
    lookup = get_chunk_lookup(telegram_id, candidate_uids)
    if not lookup:
        return []

    merged: list[dict[str, Any]] = []
    for chunk_uid in candidate_uids:
        meta = lookup.get(chunk_uid)
        if not meta:
            continue
        bm25_score = bm25_score_by_uid.get(chunk_uid, 0.0)
        semantic_score = semantic_score_by_uid.get(chunk_uid, 0.0)
        if semantic_score_by_uid:
            final = HYBRID_ALPHA * bm25_score + (1 - HYBRID_ALPHA) * semantic_score
        else:
            final = bm25_score
        merged.append(
            {
                "chunk_uid": chunk_uid,
                "content": meta["content"],
                "doc_name": meta["doc_name"],
                "score": final,
            }
        )

    merged = _apply_structured_retrieval_boosts(rows=merged, query=query)
    return merged[:top_k]


def _log_shadow_compare(
    *,
    telegram_id: int,
    old_results: list[dict[str, Any]],
    new_results: list[dict[str, Any]],
    mode: str = "hybrid_migration",
) -> None:
    """Log old/new retrieval overlap during migration."""
    old_uids = [row.get("chunk_uid") for row in old_results if row.get("chunk_uid")]
    new_uids = [row.get("chunk_uid") for row in new_results if row.get("chunk_uid")]
    intersection = len(set(old_uids) & set(new_uids))
    logger.info(
        "kb_retrieval_shadow_compare",
        extra={
            "event": "kb_retrieval_shadow_compare",
            "telegram_id": telegram_id,
            "mode": mode,
            "old_top": old_uids,
            "new_top": new_uids,
            "old_count": len(old_uids),
            "new_count": len(new_uids),
            "intersection": intersection,
        },
    )


def _invalidate_chat_context_due_to_kb_change(telegram_id: int) -> None:
    """
    Clear chat context after KB removal to avoid "ghost" answers.

    Without this, facts previously pulled from KB can remain in the rolling
    chat history or summary and continue influencing answers even after the
    underlying document has been deleted.
    """
    try:
        ctx_svc.clear_context(telegram_id)
        logger.info(
            "kb_context_invalidated",
            extra={"event": "kb_context_invalidated", "telegram_id": telegram_id},
        )
    except Exception as exc:
        logger.warning("kb_context_invalidation_failed", extra={"error": str(exc)[:200]})


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_text(filename: str, data: bytes) -> str:
    """Backward-compatible legacy text extraction wrapper."""
    return docling_svc._parse_with_legacy(
        filename,
        data,
        parser_mode="legacy_only",
    ).text


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks, preferring natural boundaries."""
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


# ── Indexing ──────────────────────────────────────────────────────────────────

def _index_text_payload(
    telegram_id: int,
    *,
    name: str,
    text: str,
    size_bytes: int,
    source_type: str = "file",
    source_url: str | None = None,
    parsed_document: docling_svc.ParsedDocument | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """
    Chunk, embed and persist normalized KB text payload.
    Returns (success, human-readable message).
    """
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден", None

    max_doc_size_bytes = get_max_doc_size_bytes()
    if size_bytes > max_doc_size_bytes:
        return False, f"Файл слишком большой (макс. {format_doc_size_limit(max_doc_size_bytes)})", None

    if kb_repo.count_documents(uid) >= MAX_DOCS_PER_USER:
        return False, (
            f"Достигнут лимит ({MAX_DOCS_PER_USER} документов). "
            "Удали лишнее через /kb"
        ), None

    text = text.strip()
    if not text:
        return False, "Документ пустой или не содержит текста", None

    chunks, chunk_metadata, ingestion_stats = _build_ingestion_chunks(
        name=name,
        text=text,
        parsed_document=parsed_document,
    )
    if not chunks:
        return False, "Не удалось разбить документ на фрагменты", None

    # Compute embeddings (optional — graceful degradation to BM25-only)
    vectors, embedding_blobs, embedding_status = _compute_embeddings_for_chunks(chunks)

    try:
        doc_id = kb_repo.add_document(
            uid,
            name,
            size_bytes,
            len(chunks),
            source_type=source_type,
            source_url=source_url,
            **_build_document_store_payload(
                parsed_document,
                ingestion_stats=ingestion_stats,
            ),
        )
        chunk_uids = kb_repo.add_chunks(
            doc_id,
            uid,
            chunks,
            embedding_blobs,
            chunk_metadata=chunk_metadata,
        )
    except Exception as exc:
        logger.warning("kb_index_failed", extra={"error": str(exc)})
        return False, "Ошибка при сохранении в базу знаний", None

    if _is_dual_write_enabled() and vectors and len(vectors) == len(chunks):
        logger.info(
            "kb_dual_write_started",
            extra={
                "event": "kb_dual_write_started",
                "telegram_id": telegram_id,
                "doc_id": doc_id,
                "chunk_count": len(chunks),
            },
        )
        vector_rows = _build_vector_rows(
            chunk_uids=chunk_uids,
            chunks=chunks,
            vectors=vectors,
        )
        try:
            written = kb_vector_repo.upsert_chunks(
                user_db_id=uid,
                doc_id=doc_id,
                chunks=vector_rows,
            )
            logger.info(
                "kb_dual_write_finished",
                extra={
                    "event": "kb_dual_write_finished",
                    "telegram_id": telegram_id,
                    "doc_id": doc_id,
                    "written": written,
                },
            )
        except Exception as exc:
            logger.warning(
                "kb_lancedb_write_failed",
                extra={
                    "event": "kb_lancedb_write_failed",
                    "telegram_id": telegram_id,
                    "doc_id": doc_id,
                    "error": str(exc)[:200],
                },
            )

    has_emb = vectors is not None
    if has_emb:
        emb_note = " + embeddings"
    elif embedding_status == "unavailable":
        emb_note = " (BM25-only, no API key)"
    else:
        emb_note = " (BM25-only, embedding request failed)"
    logger.info(
        "kb_document_indexed",
        extra={
            "event": "kb_document_indexed",
            "telegram_id": telegram_id,
            "doc_name": name,
            "chunks": len(chunks),
            "size": size_bytes,
            "has_embeddings": has_emb,
            "dual_write_enabled": _is_dual_write_enabled(),
            "legacy_embedding_written": bool(embedding_blobs),
            "embedding_status": embedding_status,
            "source_type": source_type,
            "has_source_url": bool(source_url),
            "parser_backend": getattr(parsed_document, "parser_backend", None),
            "source_format": getattr(parsed_document, "source_format", None),
            "doc_has_tables": bool(getattr(parsed_document, "has_tables", False)),
            "doc_has_headings": bool(getattr(parsed_document, "has_headings", False)),
            "pipeline_mode": ingestion_stats.get("pipeline_mode"),
            "normalized_block_count": ingestion_stats.get("normalized_block_count", 0),
            "table_count": ingestion_stats.get("table_count", 0),
            "section_count": ingestion_stats.get("section_count", 0),
            "structured_fallback_used": ingestion_stats.get("chunking_fallback_used", False),
        },
    )
    return True, f"Проиндексировано {len(chunks)} фрагментов{emb_note}", {
        "doc_id": doc_id,
        "user_db_id": uid,
    }


def index_document(telegram_id: int, filename: str, data: bytes) -> tuple[bool, str]:
    """
    Extract, chunk, embed and persist an uploaded file document.
    Returns (success, human-readable message).
    """
    kb_rollout.log_rollout_event(
        "kb_upload_received",
        telegram_id=telegram_id,
        source_type="file",
        filename=filename,
        size_bytes=len(data),
        docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
    )
    kb_rollout.log_rollout_event(
        "kb_parse_started",
        telegram_id=telegram_id,
        source_type="file",
        filename=filename,
        parser_mode=kb_rollout.get_doc_parser_mode(),
        docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
    )
    try:
        parsed = docling_svc.parse_document(
            filename,
            data,
            parser_mode=kb_rollout.get_doc_parser_mode(),
        )
    except ValueError as e:
        kb_rollout.log_rollout_event(
            "kb_upload_extract_failed",
            telegram_id=telegram_id,
            source_type="file",
            filename=filename,
            error=str(e)[:200],
            docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
        )
        return False, str(e)
    except Exception as e:
        kb_rollout.log_rollout_event(
            "kb_upload_extract_failed",
            telegram_id=telegram_id,
            source_type="file",
            filename=filename,
            error=str(e)[:200],
            docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
        )
        return False, f"Ошибка при чтении файла: {e}"

    kb_rollout.log_rollout_event(
        "kb_parse_finished",
        telegram_id=telegram_id,
        source_type="file",
        filename=filename,
        parser_mode=parsed.parser_mode,
        parser_backend=parsed.parser_backend,
        fallback_used=parsed.fallback_used,
        source_format=parsed.source_format,
        warning_count=len(parsed.warnings),
        docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
    )

    ok, msg, payload = _index_text_payload(
        telegram_id,
        name=filename,
        text=parsed.text,
        size_bytes=len(data),
        source_type="file",
        source_url=None,
        parsed_document=parsed,
    )
    summary_artifacts: doc_summary_svc.SummaryArtifacts | None = None
    if ok and payload:
        try:
            summary_artifacts = _maybe_generate_and_store_summary(
                telegram_id=telegram_id,
                user_db_id=payload["user_db_id"],
                doc_id=payload["doc_id"],
                filename=filename,
                parsed_document=parsed,
            )
        except Exception as exc:
            logger.warning(
                "kb_doc_summary_post_index_failed",
                extra={
                    "event": "kb_doc_summary_post_index_failed",
                    "telegram_id": telegram_id,
                    "error": str(exc)[:200],
                },
            )
        msg = kb_feedback_svc.build_upload_success_html(
            filename=filename,
            index_result_message=msg,
            parsed_document=parsed,
            summary_artifacts=summary_artifacts if kb_rollout.should_send_summary_after_index_success() else None,
            kb_auto_enabled=False,
        )
    kb_rollout.log_rollout_event(
        "kb_upload_index_finished",
        telegram_id=telegram_id,
        source_type="file",
        filename=filename,
        success=ok,
        docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
    )
    return ok, msg


def index_url(telegram_id: int, url: str) -> tuple[bool, str]:
    """
    Fetch, normalize and persist a web page into the shared KB.
    """
    kb_rollout.log_rollout_event(
        "kb_upload_received",
        telegram_id=telegram_id,
        source_type="url",
        source_url=url,
        docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
    )
    if not is_url_ingestion_enabled():
        kb_rollout.log_rollout_event(
            "kb_upload_blocked",
            telegram_id=telegram_id,
            source_type="url",
            source_url=url,
            reason="url_ingestion_disabled",
            docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
        )
        return False, "URL ingestion сейчас отключен."

    try:
        payload = url_ing_svc.fetch_url_document(url)
    except ValueError as exc:
        kb_rollout.log_rollout_event(
            "kb_upload_extract_failed",
            telegram_id=telegram_id,
            source_type="url",
            source_url=url,
            error=str(exc)[:200],
            docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
        )
        return False, str(exc)
    except Exception as exc:
        kb_rollout.log_rollout_event(
            "kb_upload_extract_failed",
            telegram_id=telegram_id,
            source_type="url",
            source_url=url,
            error=str(exc)[:200],
            docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
        )
        return False, f"Ошибка при обработке URL: {exc}"

    ok, msg, _payload = _index_text_payload(
        telegram_id,
        name=payload["title"],
        text=payload["text"],
        size_bytes=payload["size_bytes"],
        source_type="url",
        source_url=payload["url"],
    )
    kb_rollout.log_rollout_event(
        "kb_upload_index_finished",
        telegram_id=telegram_id,
        source_type="url",
        source_url=payload["url"],
        success=ok,
        docling_active_for_user=kb_rollout.is_docling_active_for_user(telegram_id),
    )
    return ok, msg


# ── BM25 scoring ─────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[а-яёa-z0-9]+", text.lower())


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    avgdl: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Standard BM25 term-frequency scoring."""
    dl = len(doc_tokens)
    doc_counter = Counter(doc_tokens)
    score = 0.0
    for token in set(query_tokens):
        tf = doc_counter.get(token, 0)
        if tf:
            norm_tf = tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))
            score += norm_tf
    return score


# ── Hybrid retrieval ─────────────────────────────────────────────────────────

def _normalize_scores(values: list[float]) -> list[float]:
    """Min-max normalize a list of scores to [0, 1]."""
    if not values:
        return values
    lo = min(values)
    hi = max(values)
    span = hi - lo
    if span == 0:
        return [1.0] * len(values)
    return [(v - lo) / span for v in values]


def _overlap_ratio(query_tokens: list[str], text: str | None) -> float:
    if not query_tokens or not text:
        return 0.0
    target_tokens = set(_tokenize(text))
    if not target_tokens:
        return 0.0
    matches = 0
    for query_token in set(query_tokens):
        if query_token in target_tokens:
            matches += 1
            continue
        for target_token in target_tokens:
            min_len = min(len(query_token), len(target_token))
            if min_len >= 5 and (
                query_token.startswith(target_token[:5]) or target_token.startswith(query_token[:5])
            ):
                matches += 1
                break
    return matches / max(1, len(set(query_tokens)))


def _is_table_friendly_query(query: str, query_tokens: list[str]) -> bool:
    table_tokens = {
        "таблица", "таблице", "таблицы", "табличные", "табличный",
        "значение", "значения", "параметр", "параметры", "характеристики",
        "сравнение", "сравнить", "цена", "стоимость", "процент", "размер",
        "число", "цифры",
    }
    return any(token in table_tokens for token in query_tokens) or bool(re.search(r"\d", query or ""))


def _is_page_friendly_query(query_tokens: list[str]) -> bool:
    return any(token in {"страница", "странице", "страницы", "стр", "стре"} for token in query_tokens)


def _apply_structured_retrieval_boosts(
    *,
    rows: list[dict[str, Any]],
    query: str,
) -> list[dict[str, Any]]:
    if not rows or not kb_rollout.is_structured_retrieval_enabled():
        return rows

    query_tokens = _tokenize(query)
    wants_table = _is_table_friendly_query(query, query_tokens)
    wants_page = _is_page_friendly_query(query_tokens)

    boosted: list[dict[str, Any]] = []
    for row in rows:
        score = float(row.get("score", 0.0))
        section_overlap = max(
            _overlap_ratio(query_tokens, row.get("section_title")),
            _overlap_ratio(query_tokens, " ".join(row.get("heading_path_json") or [])),
        )
        if section_overlap > 0:
            score += STRUCTURED_SECTION_BOOST * section_overlap

        if row.get("is_table"):
            score += 0.03
            if wants_table:
                score += STRUCTURED_TABLE_BOOST

        if wants_page and (row.get("page_from") is not None or row.get("page_to") is not None):
            score += STRUCTURED_PAGE_BOOST

        boosted.append({**row, "score": score})

    boosted.sort(key=lambda x: x["score"], reverse=True)
    return boosted


def _build_provenance_label(row: dict[str, Any]) -> str:
    parts = [f"Из: {row['doc_name']}"]
    section_title = row.get("section_title")
    if section_title:
        parts.append(f"Раздел: {section_title}")

    page_from = row.get("page_from")
    page_to = row.get("page_to")
    if page_from is not None and page_to is not None and page_from != page_to:
        parts.append(f"Стр.: {page_from}-{page_to}")
    elif page_from is not None:
        parts.append(f"Стр.: {page_from}")
    elif page_to is not None:
        parts.append(f"Стр.: {page_to}")

    if row.get("is_table"):
        parts.append("Таблица")
    return " | ".join(parts)


def _format_context_fragment(row: dict[str, Any], remaining_chars: int) -> str:
    fragment = row["content"]
    max_chars = min(remaining_chars, TABLE_CONTEXT_MAX_CHARS if row.get("is_table") else remaining_chars)
    if len(fragment) > max_chars:
        clipped = fragment[:max_chars]
        fragment = clipped.rsplit(" ", 1)[0] if " " in clipped else clipped
        fragment = fragment.rstrip() + "…"

    if row.get("is_table"):
        table_lines = [line.strip() for line in fragment.splitlines() if line.strip()]
        fragment = "Табличный фрагмент:\n" + "\n".join(table_lines[:8])
    return fragment


def retrieve_context(
    telegram_id: int,
    query: str,
    top_k: int = RETRIEVAL_TOP_K,
) -> list[dict[str, Any]]:
    """
    Hybrid retrieval: BM25 shortlist → embedding rerank.
    Each result: {"content": str, "doc_name": str, "score": float}
    """
    uid = _uid(telegram_id)
    if uid is None:
        return []

    try:
        chunks = kb_repo.get_all_chunks(uid)
    except Exception as exc:
        logger.warning("kb_retrieve_failed", extra={"error": str(exc)})
        return []

    if not chunks:
        return []
    if not (query or "").strip():
        return []

    backend = _get_vector_backend()
    logger.info(
        "kb_retrieval_backend_selected",
        extra={
            "event": "kb_retrieval_backend_selected",
            "telegram_id": telegram_id,
            "backend": backend,
            "query_len": len(query or ""),
            "chunk_count": len(chunks),
            "structured_retrieval_enabled": kb_rollout.is_structured_retrieval_enabled(),
            "doc_parser_mode": kb_rollout.get_doc_parser_mode(),
            "docling_active_for_user": kb_rollout.is_docling_active_for_user(telegram_id),
            "rollout_stage": kb_rollout.get_rollout_stage(),
        },
    )

    if backend == "sqlite":
        return _strip_internal_fields(_legacy_retrieve_context_from_chunks(chunks, query, top_k))

    new_results = _lancedb_retrieve_context(
        telegram_id=telegram_id,
        user_db_id=uid,
        chunks=chunks,
        query=query,
        top_k=top_k,
    )
    if backend == "lancedb":
        if _is_shadow_compare_enabled():
            old_results = _legacy_retrieve_context_from_chunks(chunks, query, top_k)
            _log_shadow_compare(
                telegram_id=telegram_id,
                old_results=old_results,
                new_results=new_results,
                mode="shadow_compare",
            )
        return _strip_internal_fields(new_results)

    # hybrid_migration: return the new path, but compare it with the legacy one
    old_results = _legacy_retrieve_context_from_chunks(chunks, query, top_k)
    _log_shadow_compare(
        telegram_id=telegram_id,
        old_results=old_results,
        new_results=new_results,
        mode="hybrid_migration",
    )
    if new_results:
        return _strip_internal_fields(new_results)
    return _strip_internal_fields(old_results)


def get_chunk_lookup(
    telegram_id: int,
    chunk_uids: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Return a lookup map keyed by chunk_uid for service-level enrichment.

    This helper is preparation for the future LanceDB-backed retrieval path,
    where semantic search returns chunk_uids and the service layer joins the
    final text/doc metadata from SQLite.
    """
    uid = _uid(telegram_id)
    if uid is None:
        return {}

    try:
        if chunk_uids is None:
            rows = kb_repo.get_all_chunks(uid)
        else:
            rows = kb_repo.get_chunks_by_uids(uid, chunk_uids)
    except Exception as exc:
        logger.warning("kb_chunk_lookup_failed", extra={"error": str(exc)})
        return {}

    return {
        row["chunk_uid"]: {
            "content": row["content"],
            "doc_name": row["doc_name"],
            "chunk_idx": row["chunk_idx"],
            "doc_id": row["doc_id"],
            "section_title": row.get("section_title"),
            "heading_path_json": row.get("heading_path_json"),
            "page_from": row.get("page_from"),
            "page_to": row.get("page_to"),
            "is_table": row.get("is_table"),
            "block_type": row.get("block_type"),
        }
        for row in rows
        if row.get("chunk_uid")
    }


def build_kb_context(telegram_id: int, query: str) -> str | None:
    """
    Build a context string to inject as an assistant note before the current turn.
    Returns None if nothing relevant is found.
    """
    payload = build_kb_context_payload(telegram_id, query)
    return payload["context"]


def build_kb_context_payload(telegram_id: int, query: str) -> dict[str, Any]:
    """
    Build both the injected KB context and user-facing provenance metadata.

    Returns:
        {
            "context": str | None,
            "results_count": int,
            "source_docs": list[str],
            "source_refs": list[dict[str, Any]],
            "used_kb": bool,
        }
    """
    results = retrieve_context(telegram_id, query)
    if not results:
        return {
            "context": None,
            "results_count": 0,
            "source_docs": [],
            "source_refs": [],
            "used_kb": False,
        }

    parts: list[str] = []
    total_chars = 0
    source_docs: list[str] = []
    source_refs: list[dict[str, Any]] = []
    seen_refs: set[tuple[Any, ...]] = set()

    for r in results:
        fragment = r["content"]
        doc = r["doc_name"]
        if doc and doc not in source_docs:
            source_docs.append(doc)
        ref_key = (
            r.get("doc_name"),
            r.get("section_title"),
            r.get("page_from"),
            r.get("page_to"),
            bool(r.get("is_table")),
            r.get("block_type"),
        )
        if ref_key not in seen_refs:
            seen_refs.add(ref_key)
            preview = _format_context_fragment(r, 160).replace("\n", " / ").strip()
            source_refs.append(
                {
                    "doc_name": r.get("doc_name"),
                    "section_title": r.get("section_title"),
                    "page_from": r.get("page_from"),
                    "page_to": r.get("page_to"),
                    "is_table": bool(r.get("is_table")),
                    "block_type": r.get("block_type"),
                    "preview": preview,
                }
            )
        remaining = RETRIEVAL_MAX_CHARS - total_chars
        if remaining < 80:
            break

        provenance = _build_provenance_label(r)
        fragment = _format_context_fragment(r, max(80, remaining - len(provenance) - 8))
        if total_chars + len(fragment) > RETRIEVAL_MAX_CHARS:
            remaining = RETRIEVAL_MAX_CHARS - total_chars
            if remaining < 80:
                break
            fragment = _format_context_fragment(r, remaining)

        parts.append(f"[{provenance}]\n{fragment}")
        total_chars += len(fragment)
        if total_chars >= RETRIEVAL_MAX_CHARS:
            break

    if not parts:
        return {
            "context": None,
            "results_count": len(results),
            "source_docs": source_docs,
            "source_refs": source_refs,
            "used_kb": False,
        }

    return {
        "context": "[Факты из базы знаний]\n\n" + "\n\n---\n\n".join(parts),
        "results_count": len(results),
        "source_docs": source_docs,
        "source_refs": source_refs,
        "used_kb": True,
    }


# ── Helpers for handlers ──────────────────────────────────────────────────────

def get_documents(telegram_id: int) -> list[dict[str, Any]]:
    uid = _uid(telegram_id)
    if uid is None:
        return []
    try:
        return kb_repo.get_documents(uid)
    except Exception as exc:
        logger.warning("kb_get_docs_failed", extra={"error": str(exc)})
        return []


def inspect_document(telegram_id: int, doc_id: int) -> dict[str, Any] | None:
    uid = _uid(telegram_id)
    if uid is None:
        return None
    doc = kb_repo.get_document(doc_id, uid)
    if not doc:
        return None
    chunks = kb_repo.get_chunks_by_doc(doc_id, uid)
    doc_metadata = dict(doc.get("doc_metadata_json") or {})
    return {
        "doc_id": doc["id"],
        "name": doc["name"],
        "source_type": doc.get("source_type"),
        "parser_backend": doc.get("parser_backend"),
        "parser_mode": doc.get("parser_mode"),
        "source_format": doc.get("source_format"),
        "parse_success": bool(doc.get("parser_backend")),
        "fallback_used": bool(doc_metadata.get("fallback_used")),
        "summary_ready": doc.get("summary_status") in {"generated", "fallback_preview"},
        "summary_status": doc.get("summary_status"),
        "metadata_richness": _document_metadata_richness(doc, chunks),
        "has_tables": bool(doc.get("doc_has_tables")),
        "has_headings": bool(doc.get("doc_has_headings")),
        "chunk_count": len(chunks),
        "table_chunk_count": sum(1 for chunk in chunks if chunk.get("is_table")),
        "summary_generated_at": doc.get("summary_generated_at"),
        "summary_error": doc.get("summary_error"),
    }


def inspect_chunks(telegram_id: int, doc_id: int, limit: int = 5) -> list[dict[str, Any]]:
    uid = _uid(telegram_id)
    if uid is None:
        return []
    chunks = kb_repo.get_chunks_by_doc(doc_id, uid)
    preview: list[dict[str, Any]] = []
    for chunk in chunks[: max(1, limit)]:
        preview.append(
            {
                "chunk_uid": chunk.get("chunk_uid"),
                "chunk_idx": chunk.get("chunk_idx"),
                "section_title": chunk.get("section_title"),
                "page_from": chunk.get("page_from"),
                "page_to": chunk.get("page_to"),
                "is_table": bool(chunk.get("is_table")),
                "block_type": chunk.get("block_type"),
                "content_preview": (chunk.get("content") or "")[:180],
            }
        )
    return preview


def get_kb_operations_snapshot(telegram_id: int | None = None) -> dict[str, Any]:
    def _metadata_dict(raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if not raw:
            return {}
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except Exception:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _aggregate(docs: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "documents_total": len(docs),
            "docling_docs": sum(1 for doc in docs if doc.get("parser_backend") == "docling"),
            "fallback_docs": sum(1 for doc in docs if bool(_metadata_dict(doc.get("doc_metadata_json")).get("fallback_used"))),
            "summary_ready_docs": sum(1 for doc in docs if doc.get("summary_status") in {"generated", "fallback_preview"}),
            "table_docs": sum(1 for doc in docs if doc.get("doc_has_tables")),
            "heading_docs": sum(1 for doc in docs if doc.get("doc_has_headings")),
        }

    if telegram_id is not None:
        return _aggregate(get_documents(telegram_id))

    with get_connection() as conn:
        docs = conn.execute(
            """
            SELECT parser_backend, doc_metadata_json, summary_status, doc_has_tables, doc_has_headings
            FROM kb_documents
            """
        ).fetchall()
    return _aggregate([dict(row) for row in docs])


def _reindex_single_document(
    *,
    telegram_id: int,
    user_db_id: int,
    doc: dict[str, Any],
    mode: str = "embeddings",
    dry_run: bool = False,
) -> tuple[bool, str, dict[str, Any] | None]:
    """
    Recompute vector entries for an existing KB document from stored chunk text.

    Returns (ok, human_message, stats_dict).
    """
    mode = (mode or "embeddings").strip().lower()
    if mode not in {"embeddings", "summary", "all"}:
        return False, f"Неизвестный режим reindex: {mode}", None

    chunks = kb_repo.get_chunks_by_doc(doc["id"], user_db_id)
    if not chunks:
        return False, "Документ не содержит фрагментов для переиндексации.", None

    logger.info(
        "kb_reindex_started",
        extra={
            "event": "kb_reindex_started",
            "telegram_id": telegram_id,
            "doc_id": doc["id"],
            "chunk_count": len(chunks),
            "mode": mode,
            "dry_run": dry_run,
        },
    )
    written = 0
    legacy_updated = 0
    summary_status = None
    metadata_backfilled = False

    if mode in {"embeddings", "all"}:
        if not emb_svc.is_available():
            return False, "Для переиндексации embeddings нужен `OPENAI_API_KEY`.", None

        chunk_texts = [row["content"] for row in chunks]
        vectors, embedding_blobs, _embedding_status = _compute_embeddings_for_chunks(chunk_texts)
        if not vectors:
            return False, "Не удалось пересчитать embeddings для документа.", None

        vector_rows = _build_vector_rows(
            chunk_uids=[row["chunk_uid"] for row in chunks],
            chunks=chunk_texts,
            vectors=vectors,
        )

        if not dry_run:
            try:
                written = kb_vector_repo.upsert_chunks(
                    user_db_id=user_db_id,
                    doc_id=doc["id"],
                    chunks=vector_rows,
                )
            except Exception as exc:
                logger.warning(
                    "kb_reindex_vector_failed",
                    extra={
                        "event": "kb_reindex_vector_failed",
                        "telegram_id": telegram_id,
                        "doc_id": doc["id"],
                        "error": str(exc)[:200],
                    },
                )
                return False, f"Не удалось обновить vector index: {exc}", None

            if embedding_blobs:
                legacy_updated = kb_repo.update_chunk_embeddings(
                    user_db_id,
                    [(row["chunk_uid"], blob) for row, blob in zip(chunks, embedding_blobs)],
                )
        else:
            written = len(vector_rows)
            legacy_updated = len(chunk_texts) if _is_legacy_embedding_write_enabled() else 0

    if mode == "all":
        _backfill_structured_metadata_from_chunks(
            user_db_id=user_db_id,
            doc=doc,
            chunks=chunks,
            dry_run=dry_run,
        )
        metadata_backfilled = True

    if mode in {"summary", "all"}:
        summary_result = _regenerate_document_summary_from_storage(
            telegram_id=telegram_id,
            user_db_id=user_db_id,
            doc=doc,
            chunks=chunks,
            dry_run=dry_run,
        )
        summary_status = summary_result.get("status")

    logger.info(
        "kb_reindex_finished",
        extra={
            "event": "kb_reindex_finished",
            "telegram_id": telegram_id,
            "doc_id": doc["id"],
            "written": written,
            "legacy_updated": legacy_updated,
            "mode": mode,
            "dry_run": dry_run,
            "summary_status": summary_status,
            "metadata_backfilled": metadata_backfilled,
        },
    )
    stats = {
        "doc_id": doc["id"],
        "doc_name": doc["name"],
        "chunk_count": len(chunks),
        "vector_written": written,
        "legacy_updated": legacy_updated,
        "summary_status": summary_status,
        "metadata_backfilled": metadata_backfilled,
        "mode": mode,
        "dry_run": dry_run,
    }
    if dry_run:
        note = f"dry-run: mode={mode}, chunks={len(chunks)}, vector_rows={written}"
        if summary_status:
            note += f", summary={summary_status}"
        if metadata_backfilled:
            note += ", structured metadata backfill planned"
        return True, f"{doc['name']}: {note}.", stats

    note_parts: list[str] = []
    if mode in {"embeddings", "all"}:
        if legacy_updated:
            note_parts.append("vector index обновлён, legacy BLOB тоже освежён")
        else:
            note_parts.append("vector index обновлён, legacy BLOB не трогали")
    if summary_status:
        note_parts.append(f"summary={summary_status}")
    if metadata_backfilled:
        note_parts.append("structured metadata backfill выполнен")
    return True, f"{doc['name']}: {len(chunks)} фрагм., " + "; ".join(note_parts) + ".", stats


def reindex_document(
    telegram_id: int,
    doc_id: int,
    *,
    mode: str = "embeddings",
    dry_run: bool = False,
) -> tuple[bool, str]:
    """
    Rebuild vector entries for one existing KB document from stored chunk text.
    """
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"

    doc = kb_repo.get_document(doc_id, uid)
    if not doc:
        return False, "Документ не найден"

    ok, msg, _stats = _reindex_single_document(
        telegram_id=telegram_id,
        user_db_id=uid,
        doc=doc,
        mode=mode,
        dry_run=dry_run,
    )
    return ok, msg


def reindex_all_documents(
    telegram_id: int,
    *,
    mode: str = "embeddings",
    dry_run: bool = False,
) -> tuple[bool, str]:
    """
    Rebuild vector entries for all existing KB documents of the user.
    """
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"

    docs = kb_repo.get_documents(uid)
    if not docs:
        return False, "В базе знаний пока нет документов для переиндексации."

    success = 0
    total_chunks = 0
    failures: list[str] = []
    for doc in docs:
        ok, _msg, stats = _reindex_single_document(
            telegram_id=telegram_id,
            user_db_id=uid,
            doc=doc,
            mode=mode,
            dry_run=dry_run,
        )
        if ok and stats:
            success += 1
            total_chunks += int(stats["chunk_count"])
        else:
            failures.append(doc["name"])

    if success == 0:
        return False, "Не удалось переиндексировать ни один документ."

    failure_note = ""
    if failures:
        preview = ", ".join(failures[:3])
        suffix = "…" if len(failures) > 3 else ""
        failure_note = f"\n\n⚠️ Не удалось: {preview}{suffix}"
    dry_note = " (dry-run)" if dry_run else ""
    return True, (
        f"Переиндексировано документов{dry_note}: {success}/{len(docs)}.\n"
        f"Режим: {mode}.\n"
        f"Обновлено фрагментов: {total_chunks}.{failure_note}"
    )


def delete_document(telegram_id: int, doc_id: int) -> tuple[bool, str]:
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"
    try:
        deleted = kb_repo.delete_document(doc_id, uid)
        if not deleted:
            return False, "Документ не найден"
        try:
            kb_vector_repo.delete_by_doc(user_db_id=uid, doc_id=doc_id)
        except Exception as cleanup_exc:
            logger.warning("kb_vector_cleanup_failed", extra={"error": str(cleanup_exc)[:200]})
        _invalidate_chat_context_due_to_kb_change(telegram_id)
        return True, "Удалено! Контекст чата очищен, чтобы забыть факты из удалённой KB."
    except Exception as exc:
        logger.warning("kb_delete_doc_failed", extra={"error": str(exc)})
        return False, "Ошибка при удалении"


def clear_all(telegram_id: int) -> None:
    uid = _uid(telegram_id)
    if uid is None:
        return
    try:
        kb_repo.delete_all_documents(uid)
        try:
            kb_vector_repo.delete_all_for_user(user_db_id=uid)
        except Exception as cleanup_exc:
            logger.warning("kb_vector_clear_failed", extra={"error": str(cleanup_exc)[:200]})
        _invalidate_chat_context_due_to_kb_change(telegram_id)
    except Exception as exc:
        logger.warning("kb_clear_all_failed", extra={"error": str(exc)})
