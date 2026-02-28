-- Migration 004: Context storage for multi-turn conversations

-- Add context mode to users: 'single' (stateless Q&A) or 'chat' (with memory)
ALTER TABLE users ADD COLUMN context_mode TEXT NOT NULL DEFAULT 'single';

-- Rolling window of conversation messages (user + assistant turns)
CREATE TABLE IF NOT EXISTS context_messages (
    id          INTEGER   PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER   NOT NULL REFERENCES users(id),
    role        TEXT      NOT NULL CHECK(role IN ('user', 'assistant')),
    content     TEXT      NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_context_messages_user_id    ON context_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_context_messages_created_at ON context_messages(created_at);

-- Compressed summary of trimmed (old) turns, to preserve conversation continuity
CREATE TABLE IF NOT EXISTS context_summary (
    user_id     INTEGER   PRIMARY KEY REFERENCES users(id),
    summary     TEXT      NOT NULL DEFAULT '',
    updated_at  TIMESTAMP NOT NULL DEFAULT (datetime('now'))
);
