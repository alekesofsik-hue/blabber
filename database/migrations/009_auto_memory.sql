-- Migration 009: Useful long-term memory suggestions (auto-remember).
--
-- Adds:
-- - user_profiles.kind: distinguishes "fact" vs "preference"
-- - users.auto_memory_enabled + last_suggested_at: per-user feature flag + cooldown
-- - memory_suggestions: persists pending suggestion items for inline callbacks

-- Categorize profile entries
ALTER TABLE user_profiles ADD COLUMN kind TEXT NOT NULL DEFAULT 'fact';

-- Per-user auto-memory settings
ALTER TABLE users ADD COLUMN auto_memory_enabled BOOLEAN NOT NULL DEFAULT 1;
ALTER TABLE users ADD COLUMN auto_memory_last_suggested_at TIMESTAMP DEFAULT NULL;

-- Pending suggestion payloads (for Telegram inline callbacks)
CREATE TABLE IF NOT EXISTS memory_suggestions (
    id         TEXT      PRIMARY KEY,
    user_id    INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    items_json TEXT      NOT NULL,
    status     TEXT      NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted','dismissed','expired')),
    created_at TIMESTAMP NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_memory_suggestions_user ON memory_suggestions(user_id);
