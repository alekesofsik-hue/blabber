-- Migration 013: KB source metadata for file/url ingestion.
--
-- Adds lightweight source metadata so KB documents can represent either
-- uploaded files or fetched web pages.

ALTER TABLE kb_documents ADD COLUMN source_type TEXT NOT NULL DEFAULT 'file';
ALTER TABLE kb_documents ADD COLUMN source_url TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_kb_docs_source_type ON kb_documents(source_type);
