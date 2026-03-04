-- Long-term memory C: RAG knowledge base.
-- Users upload documents; the bot indexes them as text chunks and retrieves
-- the most relevant fragments to inject into the LLM context when answering.

CREATE TABLE IF NOT EXISTS kb_documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    size_bytes  INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at  DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS kb_chunks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id    INTEGER NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content   TEXT    NOT NULL,
    chunk_idx INTEGER NOT NULL,
    created_at DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_kb_docs_user   ON kb_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_user ON kb_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_doc  ON kb_chunks(doc_id);
