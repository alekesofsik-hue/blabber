# Admin Panel Roadmap — Blabber Bot

> **Статус:** В активной разработке
> **Последнее обновление:** 2026-02-27
> **Принципы:** Безопасность прежде всего · Каждый спринт оставляет бота рабочим · Новый код параллелен старому до полного переключения

---

## Выполнено (краткая сводка)

Реализовано и работает в продакшене:

- **Sprint 1–5:** Database, RBAC, Dynamic Config, Telegram Admin UI, AI Limits & Usage Tracking
- **Sprint 7:** Testing & Polish (pytest, graceful degradation, rate limiting, документация)
- **OpenAI:** Интеграция модели GPT-4o/GPT-4o-mini
- **Контекст диалога:** Режимы Чат / Вопрос-ответ (`/mode`), `/reset` и `/clear`, окно 10 реплик + summary, TTL 60 мин
- **Стоимость (шаг 1):** Реальные токены из OpenAI/OpenRouter API, расчёт cost_usd в `usage_logs`

---

## Оглавление

- [Sprint A: Стоимость — конфигурируемый прайс](#sprint-a-стоимость--конфигурируемый-прайс)
- [Sprint B: Рефакторинг bot.py](#sprint-b-рефакторинг-botpy)
- [Приложение A: Схема БД (актуальная)](#приложение-a-схема-бд-актуальная)
- [Приложение B: Структура проекта](#приложение-b-структура-проекта)

---

## Sprint A: Стоимость — конфигурируемый прайс

**Цель:** Вынести прайс-лист из кода в конфиг. Расширить учёт стоимости на провайдеры, где API возвращает usage.

**Контекст:** Сейчас прайс захардкожен в `utils._PRICE_TABLE`. Реальные токены берутся только из OpenAI и OpenRouter. Для GigaChat, Yandex GPT, Ollama — cost = 0.

### Задачи

- [ ] Добавить в `config` параметр `pricing_table` (JSON)
  - Формат: `{"provider/model": {"input_per_1k": float, "output_per_1k": float}}`
  - Fallback на текущий `_PRICE_TABLE` если ключ пуст
- [ ] Миграция `005_pricing_config.sql` — INSERT OR IGNORE `pricing_table`
- [ ] В `utils.py`: читать прайс из `get_setting("pricing_table")`, парсить JSON
- [ ] Расширить расчёт cost для провайдеров, где API возвращает usage:
  - [ ] GigaChat — проверить, отдаёт ли API `usage` в ответе
  - [ ] Yandex GPT — проверить SDK/API на наличие usage
  - [ ] Ollama — в ответе часто есть `eval_count`; при наличии — использовать
- [ ] Админ: возможность просмотра/редактирования `pricing_table` через `/admin` → Конфигурация
- [ ] Документация: README — как обновлять прайс, пример JSON

### Definition of Done

> Прайс хранится в БД. Изменение `pricing_table` через `/setconfig` или меню сразу влияет на расчёт cost.
> Для всех провайдеров, где API отдаёт токены — cost считается. Для остальных — 0 (без ошибок).

---

## Sprint B: Рефакторинг bot.py

**Цель:** Чистая архитектура. `bot.py` — тонкий entry point.
Вынести хендлеры в отдельные модули.

**Контекст:** Сейчас `bot.py` содержит все хендлеры (start, help, models, model, voice, mode, reset, handle_text_message). `user_storage.py` — in-memory словари; `preferred_model` и `voice_*` дублируются в БД (`users`). Рефакторинг опционален — бот работает, но структура тяжёлая.

### Задачи

- [ ] `handlers/user_commands.py` — вынос из `bot.py`:
  - [ ] `/start`, `/help`, `/models`, `/model`, `/voice`, `/mode`, `/reset`, `/clear`
  - [ ] Функция `register_user_handlers(bot)`
- [ ] `handlers/chat_handler.py` — вынос обработки текстовых сообщений:
  - [ ] Проверка maintenance_mode, лимитов
  - [ ] Получение history из context_service
  - [ ] Вызов `get_chat_response`, сохранение turn в context
  - [ ] TTS, отправка ответа
  - [ ] Функция `register_chat_handler(bot)`
- [ ] Рефакторинг `bot.py`:
  - [ ] `init_db()` → `ConfigRegistry.load()` → `register_admin_handlers()` → `register_user_handlers()` → `register_chat_handler()` → `infinity_polling()`
  - [ ] Целевой размер: 40–60 строк
- [ ] Решение по `user_storage.py`:
  - [ ] Вариант A: оставить как кеш поверх БД (модель, voice) — быстрее, меньше запросов
  - [ ] Вариант B: убрать, читать/писать только в `users` через `user_repo`
  - [ ] Выбрать и реализовать
- [ ] Проверка: порядок регистрации хендлеров (admin → user → chat), callback-префиксы не конфликтуют

### Definition of Done

> `bot.py` — не более 60 строк. Вся логика в `handlers/`, `services/`, `repositories/`.
> Бот работает без регрессий. Все команды и сценарии (в т.ч. контекст, /mode, /reset) функционируют.

---

## Приложение A: Схема БД (актуальная)

```
┌──────────────────────────────────┐       ┌─────────────────────────┐
│             users                │       │         roles           │
├──────────────────────────────────┤       ├─────────────────────────┤
│ id            INTEGER PK         │       │ id      INTEGER PK      │
│ telegram_id   BIGINT UNIQUE      │──┐    │ name    TEXT UNIQUE     │
│ username      TEXT               │  │    │ weight  INTEGER        │
│ first_name    TEXT               │  │    └─────────────────────────┘
│ role_id       INTEGER FK ────────│──┘
│ is_active     BOOLEAN            │
│ daily_token_limit    INTEGER     │       ┌─────────────────────────┐
│ daily_request_limit  INTEGER     │       │      usage_logs          │
│ tokens_used_today    INTEGER     │       ├─────────────────────────┤
│ requests_today       INTEGER     │       │ id          INTEGER PK  │
│ limits_reset_at      TIMESTAMP   │       │ user_id     INTEGER FK ──│──► users.id
│ preferred_model      TEXT        │       │ provider    TEXT        │
│ voice_enabled        BOOLEAN     │       │ model       TEXT        │
│ voice_choice         TEXT       │       │ tokens_in   INTEGER     │
│ context_mode         TEXT       │  ◄──  │ tokens_out  INTEGER     │
│ created_at           TIMESTAMP   │  NEW │ cost_usd    REAL        │
│ updated_at           TIMESTAMP   │       │ duration_ms INTEGER    │
└──────────────────────────────────┘       │ success     BOOLEAN     │
                                          │ error_text  TEXT        │
┌──────────────────────────────────┐       │ created_at  TIMESTAMP   │
│       context_messages           │       └─────────────────────────┘
├──────────────────────────────────┤
│ id          INTEGER PK           │       ┌─────────────────────────┐
│ user_id     INTEGER FK ──────────│──►users│       config            │
│ role        TEXT (user/assistant)│       ├─────────────────────────┤
│ content     TEXT                 │       │ key, value, value_type  │
│ created_at  TIMESTAMP            │       │ category, description   │
└──────────────────────────────────┘       │ is_secret, updated_at   │
                                          └─────────────────────────┘
┌──────────────────────────────────┐
│       context_summary            │
├──────────────────────────────────┤
│ user_id     INTEGER PK FK ───────│──►users
│ summary     TEXT                 │
│ updated_at  TIMESTAMP            │
└──────────────────────────────────┘
```

---

## Приложение B: Структура проекта

```
blabber/
├── bot.py
├── utils.py
├── user_storage.py
├── telemetry.py
├── tts.py
├── database/
│   ├── engine.py
│   └── migrations/
│       ├── 001_initial.sql
│       ├── 002_config_seed.sql
│       ├── 003_openai.sql
│       └── 004_context.sql
├── repositories/
│   ├── user_repo.py
│   ├── config_repo.py
│   ├── usage_repo.py
│   └── context_repo.py
├── services/
│   ├── user_service.py
│   ├── config_registry.py
│   ├── limiter.py
│   ├── usage_service.py
│   └── context_service.py
├── handlers/
│   └── admin_commands.py
├── middleware/
│   ├── auth.py
│   └── rate_limit.py
├── llm_providers/
│   ├── openrouter.py
│   ├── openai.py
│   ├── gigachat.py
│   ├── gigachat_token.py
│   ├── yandexgpt.py
│   └── ollama.py
├── tests/
├── TESTING_MANUAL.md
├── ADMIN_ROADMAP.md
└── ...
```

---

## Отложено / Не в плане

По обсуждению **не реализуем** и не вносим в план:

- Приватность/opt-in для хранения контекста
- Долгосрочная память о пользователе (отдельно от диалога)
- Контекст для групповых чатов
- Другие «дополнительные идеи» из прошлого обсуждения
