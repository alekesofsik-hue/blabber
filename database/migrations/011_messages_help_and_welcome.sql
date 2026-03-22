-- Единый источник шаблонов по умолчанию: bot_texts/defaults.py
-- Пустое welcome_message / help_message = встроенный шаблон из кода.

-- Сброс только «заводского» приветствия из 002 (кто не менял текст вручную — получит HTML из кода)
UPDATE config SET
  value = '',
  description = 'Текст /start при переопределении из админки. Оставьте пустым — встроенный шаблон из bot_texts/defaults.py (HTML). Плейсхолдер: {model}'
WHERE key = 'welcome_message'
  AND value = 'Привет! Я Blabber — балабол, который любит трепаться и болтать! Используй /models, /model, /voice, /help.';

-- Описание для всех остальных вариантов welcome_message
UPDATE config SET
  description = 'Текст /start при переопределении из админки. Оставьте пустым — встроенный шаблон из bot_texts/defaults.py (HTML). Плейсхолдер: {model}'
WHERE key = 'welcome_message';

INSERT OR IGNORE INTO config (key, value, value_type, category, description, is_secret) VALUES
  ('help_message', '', 'str', 'messages', 'Текст /help при переопределении из админки. Оставьте пустым — встроенный шаблон из bot_texts/defaults.py (HTML).', 0);
