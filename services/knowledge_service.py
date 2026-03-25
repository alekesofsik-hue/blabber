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

Supports TXT, PDF (pypdf), DOCX (python-docx), MD out of the box.

Legacy note:
- `kb_chunks.embedding` is now optional and disabled by default for new writes.
- It can still be refreshed intentionally as a rollback buffer for `KB_VECTOR_BACKEND=sqlite`.
- The primary read path is now `LanceDB` (`KB_VECTOR_BACKEND=lancedb` by default).
"""

from __future__ import annotations

import logging
import math
import os
import re
from collections import Counter
from typing import Any

import repositories.knowledge_repo as kb_repo
import repositories.kb_vector_repo as kb_vector_repo
from repositories.user_repo import get_by_telegram_id
import services.context_service as ctx_svc
from services import embedding_service as emb_svc
from services import url_ingestion_service as url_ing_svc

logger = logging.getLogger("blabber")

# ── Tunables ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 800           # characters per chunk (up from 500 for better embedding context)
CHUNK_OVERLAP: int = 100        # overlap between consecutive chunks
MAX_DOCS_PER_USER: int = 10
MAX_DOC_SIZE_BYTES: int = 1_000_000   # 1 MB
RETRIEVAL_TOP_K: int = 3
RETRIEVAL_MAX_CHARS: int = 1_500      # total chars injected into LLM context
BM25_SHORTLIST_K: int = 10            # how many BM25 candidates to pass to reranker
HYBRID_ALPHA: float = 0.3            # weight for BM25 in final score (0.3 BM25, 0.7 embedding)


def _uid(telegram_id: int) -> int | None:
    user = get_by_telegram_id(telegram_id)
    return user["id"] if user else None


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


def _compute_embeddings_for_chunks(
    chunks: list[str],
) -> tuple[list[list[float]] | None, list[bytes | None] | None]:
    """
    Compute semantic vectors for KB chunks and optionally serialize legacy BLOBs.
    """
    if not emb_svc.is_available():
        return None, None

    vectors = emb_svc.embed_texts(chunks)
    if not vectors or len(vectors) != len(chunks):
        logger.warning("kb_embeddings_partial_fail", extra={"chunks": len(chunks)})
        return None, None

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
    return vectors, embedding_blobs


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
                        "score": final,
                    }
                )

            hybrid_scored.sort(key=lambda x: x["score"], reverse=True)
            return hybrid_scored[:top_k]

    return [
        {
            "chunk_uid": chunks[idx].get("chunk_uid"),
            "content": chunks[idx]["content"],
            "doc_name": chunks[idx]["doc_name"],
            "score": score,
        }
        for score, idx in shortlist[:top_k]
    ]


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

    bm25_score_by_uid: dict[str, float] = {}
    if shortlist:
        bm25_raw = [score for score, _ in shortlist]
        bm25_norm = _normalize_scores(bm25_raw)
        for (_, idx), score in zip(shortlist, bm25_norm):
            chunk_uid = chunks[idx].get("chunk_uid")
            if chunk_uid:
                bm25_score_by_uid[chunk_uid] = score

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

    if not semantic_results and not shortlist:
        return []
    if not semantic_results:
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

    merged.sort(key=lambda x: x["score"], reverse=True)
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
    """Extract plain text from file bytes.  Raises ValueError on unsupported/broken files."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("txt", "md"):
        for enc in ("utf-8", "cp1251", "latin-1"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")

    if ext == "pdf":
        try:
            from pypdf import PdfReader  # type: ignore
            import io
            reader = PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(p for p in pages if p.strip())
        except ImportError:
            raise ValueError(
                "Для PDF нужен пакет pypdf.\n"
                "Установи: <code>pip install pypdf</code>\n"
                "Или загрузи TXT-версию документа."
            )
        except Exception as e:
            raise ValueError(f"Не удалось прочитать PDF: {e}")

    if ext in ("docx", "doc"):
        try:
            import docx as docx_lib  # type: ignore
            import io
            doc = docx_lib.Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise ValueError(
                "Для DOCX нужен пакет python-docx.\n"
                "Установи: <code>pip install python-docx</code>\n"
                "Или загрузи TXT-версию документа."
            )
        except Exception as e:
            raise ValueError(f"Не удалось прочитать DOCX: {e}")

    # Fallback: try as plain text
    return data.decode("utf-8", errors="replace")


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
) -> tuple[bool, str]:
    """
    Chunk, embed and persist normalized KB text payload.
    Returns (success, human-readable message).
    """
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"

    if size_bytes > MAX_DOC_SIZE_BYTES:
        return False, f"Файл слишком большой (макс. {MAX_DOC_SIZE_BYTES // 1024} КБ)"

    if kb_repo.count_documents(uid) >= MAX_DOCS_PER_USER:
        return False, (
            f"Достигнут лимит ({MAX_DOCS_PER_USER} документов). "
            "Удали лишнее через /kb"
        )

    text = text.strip()
    if not text:
        return False, "Документ пустой или не содержит текста"

    chunks = chunk_text(text)
    if not chunks:
        return False, "Не удалось разбить документ на фрагменты"

    # Compute embeddings (optional — graceful degradation to BM25-only)
    vectors, embedding_blobs = _compute_embeddings_for_chunks(chunks)

    try:
        doc_id = kb_repo.add_document(
            uid,
            name,
            size_bytes,
            len(chunks),
            source_type=source_type,
            source_url=source_url,
        )
        chunk_uids = kb_repo.add_chunks(doc_id, uid, chunks, embedding_blobs)
    except Exception as exc:
        logger.warning("kb_index_failed", extra={"error": str(exc)})
        return False, "Ошибка при сохранении в базу знаний"

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
    emb_note = " + embeddings" if has_emb else " (BM25-only, no API key)"
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
            "source_type": source_type,
            "has_source_url": bool(source_url),
        },
    )
    return True, f"Проиндексировано {len(chunks)} фрагментов{emb_note}"


def index_document(telegram_id: int, filename: str, data: bytes) -> tuple[bool, str]:
    """
    Extract, chunk, embed and persist an uploaded file document.
    Returns (success, human-readable message).
    """
    try:
        text = extract_text(filename, data)
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка при чтении файла: {e}"

    return _index_text_payload(
        telegram_id,
        name=filename,
        text=text,
        size_bytes=len(data),
        source_type="file",
        source_url=None,
    )


def index_url(telegram_id: int, url: str) -> tuple[bool, str]:
    """
    Fetch, normalize and persist a web page into the shared KB.
    """
    if not is_url_ingestion_enabled():
        return False, "URL ingestion сейчас отключен."

    try:
        payload = url_ing_svc.fetch_url_document(url)
    except ValueError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Ошибка при обработке URL: {exc}"

    return _index_text_payload(
        telegram_id,
        name=payload["title"],
        text=payload["text"],
        size_bytes=payload["size_bytes"],
        source_type="url",
        source_url=payload["url"],
    )


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
        }
        for row in rows
        if row.get("chunk_uid")
    }


def build_kb_context(telegram_id: int, query: str) -> str | None:
    """
    Build a context string to inject as an assistant note before the current turn.
    Returns None if nothing relevant is found.
    """
    results = retrieve_context(telegram_id, query)
    if not results:
        return None

    parts: list[str] = []
    total_chars = 0

    for r in results:
        fragment = r["content"]
        doc = r["doc_name"]
        if total_chars + len(fragment) > RETRIEVAL_MAX_CHARS:
            remaining = RETRIEVAL_MAX_CHARS - total_chars
            if remaining < 80:
                break
            fragment = fragment[:remaining].rsplit(" ", 1)[0]

        parts.append(f"[Из: {doc}]\n{fragment}")
        total_chars += len(fragment)
        if total_chars >= RETRIEVAL_MAX_CHARS:
            break

    if not parts:
        return None

    return "[Факты из базы знаний]\n\n" + "\n\n---\n\n".join(parts)


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


def _reindex_single_document(
    *,
    telegram_id: int,
    user_db_id: int,
    doc: dict[str, Any],
) -> tuple[bool, str, dict[str, Any] | None]:
    """
    Recompute vector entries for an existing KB document from stored chunk text.

    Returns (ok, human_message, stats_dict).
    """
    chunks = kb_repo.get_chunks_by_doc(doc["id"], user_db_id)
    if not chunks:
        return False, "Документ не содержит фрагментов для переиндексации.", None
    if not emb_svc.is_available():
        return False, "Для переиндексации нужен `OPENAI_API_KEY`.", None

    chunk_texts = [row["content"] for row in chunks]
    vectors, embedding_blobs = _compute_embeddings_for_chunks(chunk_texts)
    if not vectors:
        return False, "Не удалось пересчитать embeddings для документа.", None

    vector_rows = _build_vector_rows(
        chunk_uids=[row["chunk_uid"] for row in chunks],
        chunks=chunk_texts,
        vectors=vectors,
    )

    logger.info(
        "kb_reindex_started",
        extra={
            "event": "kb_reindex_started",
            "telegram_id": telegram_id,
            "doc_id": doc["id"],
            "chunk_count": len(chunks),
        },
    )
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

    legacy_updated = 0
    if embedding_blobs:
        legacy_updated = kb_repo.update_chunk_embeddings(
            user_db_id,
            [(row["chunk_uid"], blob) for row, blob in zip(chunks, embedding_blobs)],
        )

    logger.info(
        "kb_reindex_finished",
        extra={
            "event": "kb_reindex_finished",
            "telegram_id": telegram_id,
            "doc_id": doc["id"],
            "written": written,
            "legacy_updated": legacy_updated,
        },
    )
    stats = {
        "doc_id": doc["id"],
        "doc_name": doc["name"],
        "chunk_count": len(chunks),
        "vector_written": written,
        "legacy_updated": legacy_updated,
    }
    if legacy_updated:
        note = "vector index обновлён, legacy BLOB тоже освежён"
    else:
        note = "vector index обновлён, legacy BLOB не трогали"
    return True, f"{doc['name']}: {len(chunks)} фрагм., {note}.", stats


def reindex_document(telegram_id: int, doc_id: int) -> tuple[bool, str]:
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
    )
    return ok, msg


def reindex_all_documents(telegram_id: int) -> tuple[bool, str]:
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
    return True, (
        f"Переиндексировано документов: {success}/{len(docs)}.\n"
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
