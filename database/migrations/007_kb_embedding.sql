-- Hybrid retrieval: add embedding vector storage to kb_chunks.
-- Column is nullable: chunks without embeddings fall back to BM25-only.
ALTER TABLE kb_chunks ADD COLUMN embedding BLOB DEFAULT NULL;
