-- Migration 008: Persona (role) per user, linked to prompts.json keys

-- Add current_role column to users: stores the key from prompts.json
-- Default 'assistant' matches the default_role in prompts.json
ALTER TABLE users ADD COLUMN current_role TEXT NOT NULL DEFAULT 'assistant';
