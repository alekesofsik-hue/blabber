# Admin Panel Roadmap — Blabber Bot

> **Статус:** В активной разработке
> **Последнее обновление:** 2026-03-04
> **Принципы:** Безопасность прежде всего · Каждый спринт оставляет бота рабочим · Новый код параллелен старому до полного переключения

---

## Выполнено (краткая сводка)

Реализовано и работает в продакшене:

- **Sprint 1–5:** Database, RBAC, Dynamic Config, Telegram Admin UI, AI Limits & Usage Tracking
- **Sprint 7:** Testing & Polish (pytest, graceful degradation, rate limiting, документация)
- **OpenAI:** Интеграция модели GPT-4o/GPT-4o-mini
- **Контекст диалога:** Режимы Чат / Вопрос-ответ (`/mode`), `/reset` и `/clear`, окно 10 реплик + summary, TTL 60 мин
- **Стоимость (шаг 1):** Реальные токены из OpenAI/OpenRouter API, расчёт cost_usd в `usage_logs`
- **Память D — Профиль пользователя:** `/remember`, `/profile` с inline-удалением; факты хранятся в SQLite и инжектируются в каждый запрос к LLM (миграция `005_user_profile.sql`)
- **Память C — База знаний (RAG):** загрузка TXT/PDF/DOCX/MD, чанкинг, `/kb` с inline-управлением; адаптивный system_message (миграция `006_knowledge_base.sql`)
- **Гибридный поиск (BM25 + Embeddings):** чанки хранят embedding BLOB (`007_kb_embedding.sql`); retrieval: BM25 shortlist → embedding rerank (α=0.3 BM25 + 0.7 cosine); graceful degradation на BM25-only если нет `OPENAI_API_KEY`

---

## Оглавление

- [Sprint A: Стоимость — конфигурируемый прайс](#sprint-a-стоимость--конфигурируемый-прайс)
- [Sprint B: Рефакторинг bot.py](#sprint-b-рефакторинг-botpy)
- [Sprint C: Админ-панель для памяти (профиль + KB)](#sprint-c-админ-панель-для-памяти-профиль--kb)
- [Приложение A: Схема БД (актуальная)](#приложение-a-схема-бд-актуальная)
- [Приложение B: Структура проекта](#приложение-b-структура-проекта)

---

## Sprint A: Стоимость — конфигурируемый прайс

**Цель:** Вынести прайс-лист из кода в конфиг. Расширить учёт стоимости на провайдеры, где API возвращает usage.

**Контекст:** Сейчас прайс захардкожен в `utils._PRICE_TABLE`. Реальные токены берутся только из OpenAI и OpenRouter. Для GigaChat, Yandex GPT, Ollama — cost = 0.

**Миграция:** `008_pricing_config.sql` (005–007 заняты памятью)

### Задачи

- [ ] Добавить в `config` параметр `pricing_table` (JSON)
  - Формат: `{"provider/model": {"input_per_1k": float, "output_per_1k": float}}`
  - Fallback на текущий `_PRICE_TABLE` если ключ пуст
- [ ] Миграция `008_pricing_config.sql` — INSERT OR IGNORE `pricing_table`
  - **Примечание:** 007 занята `007_kb_embedding.sql` (embedding BLOB для гибридного поиска)
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

**Контекст:** Сейчас `bot.py` содержит хендлеры start, help, models, model, voice, mode, reset, handle_text_message, а также функцию `_build_system_message`. После добавления профиля и KB файл вырос. `user_storage.py` — in-memory словари; `preferred_model` и `voice_*` дублируются в БД (`users`). Рефакторинг опционален — бот работает, но структура тяжёлая.

### Задачи

- [ ] `handlers/user_commands.py` — вынос из `bot.py`:
  - [ ] `/start`, `/help`, `/models`, `/model`, `/voice`, `/mode`, `/reset`, `/clear`
  - [ ] Функция `register_user_handlers(bot)`
- [ ] `handlers/chat_handler.py` — вынос обработки текстовых сообщений:
  - [ ] Проверка maintenance_mode, лимитов
  - [ ] Сборка трёхслойного контекста (профиль + история + KB)
  - [ ] Вызов `get_chat_response` с адаптивным `system_message`
  - [ ] TTS, отправка ответа
  - [ ] Функция `register_chat_handler(bot)`
- [ ] Перенос `_build_system_message` в `utils.py` или `services/message_builder.py`
- [ ] Рефакторинг `bot.py`:
  - [ ] `init_db()` → `ConfigRegistry.load()` → register handlers (admin → profile → knowledge → user → chat) → `infinity_polling()`
  - [ ] Целевой размер: 40–60 строк
- [ ] Решение по `user_storage.py`:
  - [ ] Вариант A: оставить как кеш поверх БД (модель, voice, kb_enabled) — быстрее, меньше запросов
  - [ ] Вариант B: убрать, читать/писать только в `users` через `user_repo`; `kb_enabled` — в отдельную таблицу
  - [ ] Выбрать и реализовать
- [ ] Проверка: порядок регистрации хендлеров, callback-префиксы не конфликтуют (`admin_`, `ctx_`, `profile_`, `kb_`)

### Definition of Done

> `bot.py` — не более 60 строк. Вся логика в `handlers/`, `services/`, `repositories/`.
> Бот работает без регрессий. Все команды и сценарии функционируют.

---

## Sprint C: Админ-панель для памяти (профиль + KB)

**Цель:** Дать администратору видимость и контроль над новыми слоями памяти. Добавить конфигурируемые лимиты в БД вместо хардкода.

**Контекст:** Константы `MAX_FACTS`, `MAX_DOCS_PER_USER`, `MAX_DOC_SIZE_BYTES`, `RETRIEVAL_TOP_K`, `CHUNK_SIZE` сейчас захардкожены в `services/profile_service.py` и `services/knowledge_service.py`. Админ не видит, у кого есть профиль или документы.

### Задачи

#### C.1 — Конфигурируемые лимиты памяти

- [ ] Добавить в `config` (через миграцию `007_memory_config.sql` или расширение `002_config_seed.sql`):
  | Ключ | По умолчанию | Описание |
  |------|-------------|---------|
  | `profile_max_facts` | 20 | Лимит фактов на пользователя |
  | `profile_max_fact_len` | 300 | Лимит символов на факт |
  | `kb_max_docs` | 10 | Лимит документов на пользователя |
  | `kb_max_doc_size_kb` | 1024 | Лимит размера документа (КБ) |
  | `kb_retrieval_top_k` | 3 | Сколько чанков подтягивать при поиске |
  | `kb_chunk_size` | 800 | Размер чанка при индексации |
  | `kb_retrieval_max_chars` | 1500 | Макс. символов в инжектируемом KB-контексте |

- [ ] В `profile_service.py` и `knowledge_service.py`: читать лимиты через `get_setting(...)` вместо констант
- [ ] Отобразить в меню `/admin` → Конфигурация → категория `memory`

#### C.2 — Статистика памяти в `/admin`

- [ ] Добавить раздел **🧠 Память** в inline-меню `/admin`:
  ```
  🧠 Память
  ├── Профили: N пользователей, M фактов всего
  └── База знаний: N пользователей, M документов, K фрагментов
  ```
- [ ] Для реализации добавить агрегатные запросы в `repositories/profile_repo.py` и `repositories/knowledge_repo.py`:
  - `count_users_with_facts()` — сколько пользователей используют профиль
  - `count_total_facts()` — суммарно фактов в системе
  - `count_users_with_docs()` — сколько пользователей используют KB
  - `count_total_docs()` / `count_total_chunks()` — суммарная статистика

#### C.3 — Карточка пользователя: память

- [ ] В admin-меню «👥 Пользователи» → карточка пользователя — добавить строки:
  - `🧠 Профиль: N фактов` (или «нет»)
  - `📚 База знаний: N документов, M фрагментов` (или «нет»)
- [ ] Кнопки действий в карточке:
  - `🗑 Сбросить профиль` — вызывает `profile_repo.delete_all_facts(uid)` + подтверждение
  - `🗑 Очистить базу знаний` — вызывает `knowledge_repo.delete_all_documents(uid)` + подтверждение

#### C.4 — Поле has_rag в usage_logs (опционально)

- [ ] Миграция: добавить `has_profile BOOLEAN` и `has_rag BOOLEAN` в `usage_logs`
- [ ] В `utils.py` / `bot.py` → `log_request(...)` — передавать флаги
- [ ] В статистике `/admin` → Статистика — показывать, какой % запросов использует память

### Definition of Done

> Лимиты памяти управляются через `/admin` → Конфигурация без правки кода и перезапуска.
> В разделе `/admin` → Память виден суммарный охват и объём.
> В карточке пользователя виден профиль и KB; администратор может сбросить их.

---

## Приложение A: Схема БД (актуальная)

```
┌─────────────────────────────────┐       ┌─────────────────────────┐
│             users               │       │         roles           │
├─────────────────────────────────┤       ├─────────────────────────┤
│ id            INTEGER PK        │       │ id      INTEGER PK      │
│ telegram_id   BIGINT UNIQUE     │──┐    │ name    TEXT UNIQUE     │
│ username      TEXT              │  │    │ weight  INTEGER         │
│ first_name    TEXT              │  │    └─────────────────────────┘
│ role_id       INTEGER FK ───────│──┘
│ is_active     BOOLEAN           │
│ daily_token_limit    INTEGER    │       ┌─────────────────────────┐
│ daily_request_limit  INTEGER    │       │      usage_logs         │
│ tokens_used_today    INTEGER    │       ├─────────────────────────┤
│ requests_today       INTEGER    │       │ id          INTEGER PK  │
│ limits_reset_at      TIMESTAMP  │       │ user_id     INTEGER FK ─│──► users.id
│ preferred_model      TEXT       │       │ provider    TEXT        │
│ voice_enabled        BOOLEAN    │       │ model       TEXT        │
│ voice_choice         TEXT       │       │ tokens_in   INTEGER     │
│ context_mode         TEXT       │       │ tokens_out  INTEGER     │
│ created_at           TIMESTAMP  │       │ cost_usd    REAL        │
│ updated_at           TIMESTAMP  │       │ duration_ms INTEGER     │
└─────────────────────────────────┘       │ success     BOOLEAN     │
                                          │ error_text  TEXT        │
┌─────────────────────────────────┐       │ created_at  TIMESTAMP   │
│       context_messages          │       └─────────────────────────┘
├─────────────────────────────────┤
│ id          INTEGER PK          │       ┌─────────────────────────┐
│ user_id     INTEGER FK ─────────│──►    │         config          │
│ role        TEXT                │ users ├─────────────────────────┤
│ content     TEXT                │       │ key, value, value_type  │
│ created_at  TIMESTAMP           │       │ category, description   │
└─────────────────────────────────┘       │ is_secret, updated_at   │
                                          └─────────────────────────┘
┌─────────────────────────────────┐
│       context_summary           │
├─────────────────────────────────┤
│ user_id     INTEGER PK FK ──────│──► users
│ summary     TEXT                │
│ updated_at  TIMESTAMP           │
└─────────────────────────────────┘

┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│        user_profiles            │       │          kb_documents           │
│      (память D — профиль)       │       │        (память C — RAG)         │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ id         INTEGER PK           │       │ id          INTEGER PK          │
│ user_id    INTEGER FK ──────────│──►    │ user_id     INTEGER FK ─────────│──► users
│ fact       TEXT                 │ users │ name        TEXT                │
│ created_at TIMESTAMP            │       │ size_bytes  INTEGER             │
│ UNIQUE(user_id, fact)           │       │ chunk_count INTEGER             │
└─────────────────────────────────┘       │ created_at  TIMESTAMP           │
                                          └─────────────────────────────────┘
                                                          │ ON DELETE CASCADE
                                          ┌─────────────────────────────────┐
                                          │           kb_chunks             │
                                          ├─────────────────────────────────┤
                                          │ id        INTEGER PK            │
                                          │ doc_id    INTEGER FK ───────────│──► kb_documents
                                          │ user_id   INTEGER FK ───────────│──► users
                                          │ content   TEXT                  │
                                          │ chunk_idx INTEGER               │
                                          │ embedding BLOB (nullable)       │  ← 007_kb_embedding
                                          │ created_at TIMESTAMP            │
                                          └─────────────────────────────────┘
```

---

## Приложение B: Структура проекта

```
blabber/
├── bot.py                         # Entry point; регистрация хендлеров; _build_system_message
├── utils.py                       # get_chat_response() — маршрутизация, учёт токенов
├── user_storage.py                # In-memory: модель, voice, kb_enabled
├── telemetry.py
├── tts.py
├── database/
│   ├── engine.py
│   └── migrations/
│       ├── 001_initial.sql
│       ├── 002_config_seed.sql
│       ├── 003_openai.sql
│       ├── 004_context.sql
│       ├── 005_user_profile.sql   # ← память D
│       ├── 006_knowledge_base.sql # ← память C / RAG
│       └── 007_kb_embedding.sql  # ← embedding BLOB для гибридного поиска
├── repositories/
│   ├── user_repo.py
│   ├── config_repo.py
│   ├── usage_repo.py
│   ├── context_repo.py
│   ├── profile_repo.py            # ← память D
│   └── knowledge_repo.py          # ← память C / RAG
├── services/
│   ├── user_service.py
│   ├── config_registry.py
│   ├── limiter.py
│   ├── usage_service.py
│   ├── context_service.py
│   ├── profile_service.py         # ← память D
│   ├── knowledge_service.py       # ← память C / RAG (hybrid BM25 + embedding)
│   └── embedding_service.py      # ← OpenAI embeddings, cosine, BLOB serde
├── handlers/
│   ├── admin_commands.py
│   ├── profile_commands.py        # ← /remember, /profile
│   └── knowledge_commands.py      # ← /kb, загрузка документов
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
- Контекст для групповых чатов
- Другие «дополнительные идеи» из прошлого обсуждения
