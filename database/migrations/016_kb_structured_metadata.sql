-- Sprint 2: structured document and chunk metadata for KB storage.
-- SQLite becomes the source of truth for document-level and chunk-level
-- structure. LanceDB schema remains unchanged at this stage.

ALTER TABLE kb_documents ADD COLUMN parser_backend TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN parser_mode TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN parser_version TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN source_format TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN doc_structure_json TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN doc_metadata_json TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN doc_has_tables INTEGER NOT NULL DEFAULT 0;
ALTER TABLE kb_documents ADD COLUMN doc_has_headings INTEGER NOT NULL DEFAULT 0;
ALTER TABLE kb_documents ADD COLUMN doc_page_count INTEGER DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN summary_text TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN summary_topics_json TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN summary_questions_json TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN summary_status TEXT NOT NULL DEFAULT 'pending';

ALTER TABLE kb_chunks ADD COLUMN section_title TEXT DEFAULT NULL;
ALTER TABLE kb_chunks ADD COLUMN heading_path_json TEXT DEFAULT NULL;
ALTER TABLE kb_chunks ADD COLUMN page_from INTEGER DEFAULT NULL;
ALTER TABLE kb_chunks ADD COLUMN page_to INTEGER DEFAULT NULL;
ALTER TABLE kb_chunks ADD COLUMN block_type TEXT DEFAULT NULL;
ALTER TABLE kb_chunks ADD COLUMN is_table INTEGER NOT NULL DEFAULT 0;
ALTER TABLE kb_chunks ADD COLUMN table_id TEXT DEFAULT NULL;
ALTER TABLE kb_chunks ADD COLUMN meta_json TEXT DEFAULT NULL;
