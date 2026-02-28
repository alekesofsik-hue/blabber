-- Migration 003: Add OpenAI model support

INSERT OR IGNORE INTO config (key, value, value_type, category, description, is_secret) VALUES
    ('openai_model', 'gpt-4o-mini', 'str', 'models', 'OpenAI model name (gpt-4o-mini, gpt-4o, gpt-4-turbo)', 0);
