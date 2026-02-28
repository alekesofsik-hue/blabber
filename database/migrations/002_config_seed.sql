-- Migration 002: Seed initial config values
-- These can be overridden at runtime without restarting the bot

INSERT OR IGNORE INTO config (key, value, value_type, category, description, is_secret) VALUES
    ('default_model', 'openrouter', 'str', 'models', 'Default LLM model for new users', 0),
    ('default_daily_token_limit', '50000', 'int', 'limits', 'Default daily token limit per user', 0),
    ('default_daily_request_limit', '100', 'int', 'limits', 'Default daily request limit per user', 0),
    ('tts_max_chars', '5000', 'int', 'tts', 'Max characters for TTS synthesis', 0),
    ('maintenance_mode', 'false', 'bool', 'system', 'Bot in maintenance mode (reject user requests)', 0),
    ('welcome_message', 'Привет! Я Blabber — балабол, который любит трепаться и болтать! Используй /models, /model, /voice, /help.', 'str', 'messages', 'Welcome message for /start', 0),
    ('models_enabled', '{"gigachat":true,"openrouter":true,"reasoning":true,"yandexgpt":true,"ollama":true}', 'json', 'models', 'Which models are enabled for selection', 0),
    ('ollama_model', 'gemma2:2b-instruct-q4_K_M', 'str', 'models', 'Ollama model name', 0),
    ('ollama_timeout', '180', 'int', 'models', 'Ollama request timeout (seconds)', 0),
    ('ollama_num_predict', '256', 'int', 'models', 'Ollama max tokens', 0);
