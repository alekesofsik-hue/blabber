-- Sprint 0: rollout and observability flags for Docling-backed KB upgrades.
-- Default state is conservative: new behaviour is disabled until explicitly
-- enabled through config or environment variables.

INSERT OR IGNORE INTO config (key, value, value_type, category, description, is_secret) VALUES
    ('kb_docling_enabled', 'false', 'bool', 'kb', 'Enable Docling-based parsing for KB file uploads', 0),
    ('kb_docling_fallback_enabled', 'true', 'bool', 'kb', 'Allow fallback to legacy KB parser when Docling parsing fails', 0),
    ('kb_docling_rollout_stage', 'legacy', 'str', 'kb', 'Docling rollout stage: legacy, local, test, canary, global', 0),
    ('kb_docling_canary_telegram_ids', '[]', 'json', 'kb', 'Telegram IDs allowed to use Docling during canary rollout stage', 0),
    ('kb_docling_structured_chunks_enabled', 'false', 'bool', 'kb', 'Enable structured chunk building from Docling document structure', 0),
    ('kb_doc_summary_enabled', 'false', 'bool', 'kb', 'Enable post-ingest document summary, topics and suggested questions', 0),
    ('kb_doc_summary_save_enabled', 'false', 'bool', 'kb', 'Persist generated document summary artifacts in KB metadata storage', 0),
    ('kb_structured_retrieval_enabled', 'false', 'bool', 'kb', 'Enable retrieval logic that uses structured section/page/table metadata', 0);
