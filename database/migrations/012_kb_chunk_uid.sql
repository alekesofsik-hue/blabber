-- Migration 012: add stable external chunk identifiers for KB migration to LanceDB.
--
-- Goals:
-- 1. Each KB chunk gets a stable chunk_uid shared with the future vector store
-- 2. Existing rows are backfilled in-place without changing user-visible behaviour
-- 3. Keep legacy embedding BLOB path intact during the migration period

ALTER TABLE kb_chunks ADD COLUMN chunk_uid TEXT;

UPDATE kb_chunks
SET chunk_uid = lower(hex(randomblob(16)))
WHERE chunk_uid IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_kb_chunks_uid ON kb_chunks(chunk_uid);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_user_doc_uid ON kb_chunks(user_id, doc_id, chunk_uid);
