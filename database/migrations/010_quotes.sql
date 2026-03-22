-- Migration 010: Quotes collection — "Смешные фразы Балабола"
--
-- Adds a metadata table for the quotes feature.
-- Actual vectors are stored in LanceDB (file-based, per-user).
-- This table keeps lightweight metadata for listing, random picks, stats.

CREATE TABLE IF NOT EXISTS quotes (
    id         INTEGER   PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lance_id   TEXT      NOT NULL,          -- UUID, shared key with LanceDB record
    text       TEXT      NOT NULL,
    added_at   TIMESTAMP NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_quotes_user ON quotes(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_lance ON quotes(lance_id);
