-- Sprint 0 follow-up: configurable KB upload size limit.
-- Default is raised to 3 MiB and can be changed via /admin or /setconfig.

INSERT OR IGNORE INTO config (key, value, value_type, category, description, is_secret) VALUES
    ('kb_max_doc_size_kb', '3072', 'int', 'kb', 'Maximum uploaded KB document size in KiB', 0);
