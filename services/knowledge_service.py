"""
Knowledge service — long-term memory C (RAG).

Pipeline:
  Upload → extract text → chunk → compute embeddings → store in SQLite
  Query  → BM25 shortlist → embedding rerank → inject top-K into LLM context

Hybrid retrieval strategy:
  1. BM25 — lexical shortlist (cheap, keyword match) → top BM25_SHORTLIST_K
  2. Embedding cosine similarity — semantic rerank of the shortlist
  3. Final score = α * norm(BM25) + (1-α) * cosine_sim

Graceful degradation: if embeddings are unavailable (no API key, API error)
the system falls back to BM25-only retrieval — quality degrades but nothing breaks.

Supports TXT, PDF (pypdf), DOCX (python-docx), MD out of the box.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Any

import repositories.knowledge_repo as kb_repo
from repositories.user_repo import get_by_telegram_id
from services import embedding_service as emb_svc

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

def index_document(telegram_id: int, filename: str, data: bytes) -> tuple[bool, str]:
    """
    Extract, chunk, embed and persist a document.
    Returns (success, human-readable message).
    """
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"

    if len(data) > MAX_DOC_SIZE_BYTES:
        return False, f"Файл слишком большой (макс. {MAX_DOC_SIZE_BYTES // 1024} КБ)"

    if kb_repo.count_documents(uid) >= MAX_DOCS_PER_USER:
        return False, (
            f"Достигнут лимит ({MAX_DOCS_PER_USER} документов). "
            "Удали лишнее через /kb"
        )

    try:
        text = extract_text(filename, data)
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка при чтении файла: {e}"

    text = text.strip()
    if not text:
        return False, "Документ пустой или не содержит текста"

    chunks = chunk_text(text)
    if not chunks:
        return False, "Не удалось разбить документ на фрагменты"

    # Compute embeddings (optional — graceful degradation to BM25-only)
    embedding_blobs: list[bytes | None] | None = None
    if emb_svc.is_available():
        vectors = emb_svc.embed_texts(chunks)
        if vectors and len(vectors) == len(chunks):
            embedding_blobs = [emb_svc.vector_to_blob(v) for v in vectors]
            logger.info("kb_embeddings_computed", extra={"chunks": len(chunks)})
        else:
            logger.warning("kb_embeddings_partial_fail", extra={"chunks": len(chunks)})

    try:
        doc_id = kb_repo.add_document(uid, filename, len(data), len(chunks))
        kb_repo.add_chunks(doc_id, uid, chunks, embedding_blobs)
    except Exception as exc:
        logger.warning("kb_index_failed", extra={"error": str(exc)})
        return False, "Ошибка при сохранении в базу знаний"

    has_emb = embedding_blobs is not None
    emb_note = " + embeddings" if has_emb else " (BM25-only, no API key)"
    logger.info(
        "kb_document_indexed",
        extra={
            "event": "kb_document_indexed",
            "telegram_id": telegram_id,
            "doc_name": filename,
            "chunks": len(chunks),
            "size": len(data),
            "has_embeddings": has_emb,
        },
    )
    return True, f"Проиндексировано {len(chunks)} фрагментов{emb_note}"


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

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    # ── Stage 1: BM25 scoring on all chunks ───────────────────────────────
    tokenized = [_tokenize(c["content"]) for c in chunks]
    avgdl = sum(len(t) for t in tokenized) / len(tokenized)

    bm25_scored: list[tuple[float, int]] = []
    for i, tokens in enumerate(tokenized):
        score = _bm25_score(query_tokens, tokens, avgdl)
        if score > 0:
            bm25_scored.append((score, i))

    if not bm25_scored:
        return []

    bm25_scored.sort(key=lambda x: x[0], reverse=True)
    shortlist = bm25_scored[:BM25_SHORTLIST_K]

    # ── Stage 2: Embedding rerank (if available) ──────────────────────────
    has_embeddings = any(chunks[idx].get("embedding") for _, idx in shortlist)

    if has_embeddings and emb_svc.is_available():
        query_vec = emb_svc.embed_single(query)
        if query_vec:
            bm25_raw = [s for s, _ in shortlist]
            bm25_norm = _normalize_scores(bm25_raw)

            hybrid_scored: list[tuple[float, int]] = []
            for (bm25_s_raw, idx), bm25_n in zip(shortlist, bm25_norm):
                emb_blob = chunks[idx].get("embedding")
                if emb_blob:
                    chunk_vec = emb_svc.blob_to_vector(emb_blob)
                    cos_sim = emb_svc.cosine_similarity(query_vec, chunk_vec)
                    final = HYBRID_ALPHA * bm25_n + (1 - HYBRID_ALPHA) * cos_sim
                else:
                    final = bm25_n
                hybrid_scored.append((final, idx))

            hybrid_scored.sort(key=lambda x: x[0], reverse=True)
            return [
                {
                    "content": chunks[idx]["content"],
                    "doc_name": chunks[idx]["doc_name"],
                    "score": score,
                }
                for score, idx in hybrid_scored[:top_k]
            ]

    # ── Fallback: BM25-only ranking ───────────────────────────────────────
    return [
        {
            "content": chunks[idx]["content"],
            "doc_name": chunks[idx]["doc_name"],
            "score": score,
        }
        for score, idx in shortlist[:top_k]
    ]


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


def delete_document(telegram_id: int, doc_id: int) -> tuple[bool, str]:
    uid = _uid(telegram_id)
    if uid is None:
        return False, "Пользователь не найден"
    try:
        deleted = kb_repo.delete_document(doc_id, uid)
        if not deleted:
            return False, "Документ не найден"
        return True, "Удалено!"
    except Exception as exc:
        logger.warning("kb_delete_doc_failed", extra={"error": str(exc)})
        return False, "Ошибка при удалении"


def clear_all(telegram_id: int) -> None:
    uid = _uid(telegram_id)
    if uid is None:
        return
    try:
        kb_repo.delete_all_documents(uid)
    except Exception as exc:
        logger.warning("kb_clear_all_failed", extra={"error": str(exc)})
