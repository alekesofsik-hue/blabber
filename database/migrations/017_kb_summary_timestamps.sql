-- Sprint 4: summary artifact timestamps and error storage.

ALTER TABLE kb_documents ADD COLUMN summary_generated_at TEXT DEFAULT NULL;
ALTER TABLE kb_documents ADD COLUMN summary_error TEXT DEFAULT NULL;
