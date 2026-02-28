-- Migration 001: Initial schema
-- Creates core tables: roles, users, config, usage_logs

-- ============================================================
-- Roles — справочник ролей с числовым весом для RBAC
-- ============================================================
CREATE TABLE IF NOT EXISTS roles (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT    NOT NULL UNIQUE,
    weight  INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO roles (name, weight) VALUES ('user', 0);
INSERT OR IGNORE INTO roles (name, weight) VALUES ('moderator', 50);
INSERT OR IGNORE INTO roles (name, weight) VALUES ('admin', 100);


-- ============================================================
-- Users — пользователи бота (связаны с Telegram ID)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  INTEGER   PRIMARY KEY AUTOINCREMENT,
    telegram_id         BIGINT    NOT NULL UNIQUE,
    username            TEXT,
    first_name          TEXT,
    role_id             INTEGER   NOT NULL DEFAULT 1 REFERENCES roles(id),
    is_active           BOOLEAN   NOT NULL DEFAULT 1,
    daily_token_limit   INTEGER   NOT NULL DEFAULT 50000,
    daily_request_limit INTEGER   NOT NULL DEFAULT 100,
    tokens_used_today   INTEGER   NOT NULL DEFAULT 0,
    requests_today      INTEGER   NOT NULL DEFAULT 0,
    limits_reset_at     TIMESTAMP NOT NULL DEFAULT (datetime('now')),
    preferred_model     TEXT      NOT NULL DEFAULT 'openrouter',
    voice_enabled       BOOLEAN   NOT NULL DEFAULT 0,
    voice_choice        TEXT      NOT NULL DEFAULT 'alena',
    created_at          TIMESTAMP NOT NULL DEFAULT (datetime('now')),
    updated_at          TIMESTAMP NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);


-- ============================================================
-- Config — динамическая конфигурация (key-value с типизацией)
-- ============================================================
CREATE TABLE IF NOT EXISTS config (
    key         TEXT      PRIMARY KEY,
    value       TEXT      NOT NULL,
    value_type  TEXT      NOT NULL DEFAULT 'str',
    category    TEXT      NOT NULL DEFAULT 'general',
    description TEXT,
    is_secret   BOOLEAN   NOT NULL DEFAULT 0,
    updated_at  TIMESTAMP NOT NULL DEFAULT (datetime('now')),
    updated_by  BIGINT    REFERENCES users(telegram_id)
);


-- ============================================================
-- Usage Logs — журнал вызовов LLM-провайдеров
-- ============================================================
CREATE TABLE IF NOT EXISTS usage_logs (
    id          INTEGER   PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER   NOT NULL REFERENCES users(id),
    provider    TEXT      NOT NULL,
    model       TEXT      NOT NULL,
    tokens_in   INTEGER   NOT NULL DEFAULT 0,
    tokens_out  INTEGER   NOT NULL DEFAULT 0,
    cost_usd    REAL      NOT NULL DEFAULT 0.0,
    duration_ms INTEGER,
    success     BOOLEAN   NOT NULL DEFAULT 1,
    error_text  TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id    ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_logs_provider   ON usage_logs(provider);
