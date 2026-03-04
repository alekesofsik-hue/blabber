-- Long-term memory D: personal facts about each user for personalization.
-- These facts get injected into every LLM request so the bot "remembers" the user
-- across sessions, model switches, and context resets.

CREATE TABLE IF NOT EXISTS user_profiles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fact       TEXT    NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')),
    UNIQUE(user_id, fact)
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON user_profiles(user_id);
