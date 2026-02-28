# Blabber — Telegram-бот "Балабол"

Telegram-бот, который выполняет роль "балабола" — много говорит, любит трепаться и болтать, но не всегда прав и может давать пустую болтовню. Бот поддерживает шесть LLM-моделей, два режима диалога (с памятью и без), голосовую озвучку ответов и полноценную Telegram-нативную панель администрирования.

## Возможности

- ✅ **6 LLM-моделей**: OpenRouter (DeepSeek), DeepSeek R1, GigaChat, OpenAI (GPT-4o), Yandex GPT, Ollama (local)
- ✅ **Режим разговора с памятью** (`/mode chat`) — бот помнит контекст диалога
- ✅ **Режим вопрос-ответ** (`/mode single`) — каждый запрос независимый (по умолчанию)
- ✅ Переключение между моделями в любой момент, контекст при этом сохраняется
- ✅ Озвучка ответов голосовыми сообщениями (TTS, Yandex SpeechKit)
- ✅ Система администрирования: роли, лимиты, конфиг, статистика
- ✅ Учёт стоимости запросов (реальные токены для OpenAI/OpenRouter)
- ✅ Автоматический запуск через systemd

## Требования

- Python 3.10+
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- API ключи для выбранных моделей:
  - **OpenRouter / DeepSeek R1**: `PROXY_API_KEY` (api.proxyapi.ru) — один ключ на обе модели
  - **GigaChat**: `GIGACHAT_CREDENTIALS` (client_id:client_secret)
  - **OpenAI**: `OPENAI_API_KEY` (platform.openai.com)
  - **Yandex GPT**: `YANDEX_API_KEY` + `YANDEX_FOLDER_ID` (Yandex Cloud)
  - **Ollama**: локально установленный Ollama и скачанная модель

## Установка

1. **Создайте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Создайте файл `.env`** на основе `env.example`:
   ```bash
   cp env.example .env
   ```

4. **Отредактируйте `.env`** — укажите токены:
   ```env
   # Обязательно
   TELEGRAM_TOKEN=your_telegram_bot_token_here

   # Администратор(ы) — Telegram ID через запятую
   ADMIN_TELEGRAM_IDS=123456789

   # OpenRouter (DeepSeek Chat + DeepSeek R1)
   PROXY_API_KEY=your_proxy_api_key_here

   # GigaChat (опционально)
   GIGACHAT_CREDENTIALS=client_id:client_secret
   GIGACHAT_VERIFY_SSL=false

   # OpenAI (опционально)
   OPENAI_API_KEY=sk-your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini

   # Yandex GPT (опционально)
   YANDEX_API_KEY=your_yandex_api_key_here
   YANDEX_FOLDER_ID=your_yandex_folder_id_here
   YANDEX_MODEL=yandexgpt

   # Ollama (опционально)
   OLLAMA_BASE_URL=http://127.0.0.1:11434
   OLLAMA_MODEL=gemma2:2b-instruct-q4_K_M
   OLLAMA_TIMEOUT=180
   OLLAMA_NUM_PREDICT=256

   # Better Stack Logs (опционально)
   BETTERSTACK_SOURCE_TOKEN=your_token
   BETTERSTACK_INGEST_HOST=your_host
   TELEMETRY_USER_HASH_SALT=change_me
   TELEMETRY_LEVEL=INFO
   ```

5. **Запустите бота:**
   ```bash
   python bot.py
   ```
   При первом запуске SQLite-база создаётся автоматически, все миграции применяются.

---

## Команды пользователя

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и начало работы |
| `/help` | Справка по командам |
| `/models` | Список доступных моделей |
| `/model <название>` | Переключить модель |
| `/mode` | Показать режим диалога (с памятью / без) |
| `/mode chat` | Включить режим с памятью |
| `/mode single` | Включить режим вопрос-ответ |
| `/reset` или `/clear` | Очистить историю разговора |
| `/voice` | Показать статус и настройки озвучки |
| `/voice on` / `/voice off` | Включить / выключить озвучку |
| `/voice alena` / `/voice filipp` | Выбрать голос |

### Доступные модели

| Команда | Модель | Ключ |
|---------|--------|------|
| `/model openrouter` | DeepSeek Chat (по умолчанию) | `PROXY_API_KEY` |
| `/model reasoning` | DeepSeek R1 (рассуждающая) | `PROXY_API_KEY` |
| `/model gigachat` | GigaChat (Сбер) | `GIGACHAT_CREDENTIALS` |
| `/model openai` | GPT-4o-mini / GPT-4o | `OPENAI_API_KEY` |
| `/model yandexgpt` | Yandex GPT | `YANDEX_API_KEY` + `YANDEX_FOLDER_ID` |
| `/model ollama` | Локальная модель | Ollama на `OLLAMA_BASE_URL` |

---

## Режим разговора (контекст)

Бот поддерживает два режима:

- **Вопрос-ответ** (`/mode single`) — каждое сообщение обрабатывается независимо. **По умолчанию.**
- **Чат** (`/mode chat`) — бот помнит историю диалога (окно 10 реплик + сжатое резюме).

Переключить можно командой (`/mode chat`, `/mode single`) или через меню `/mode`.

При смене модели (`/model ...`) история диалога **не сбрасывается** — контекст общий для всех моделей.

**TTL**: если молчать более 60 минут, история автоматически очищается.

**Очистка**: `/reset` или `/clear` — спросит подтверждение, затем сотрёт историю и резюме.

---

## Озвучка ответов (TTS)

Бот озвучивает ответы голосовыми сообщениями Telegram («кружки с волной»).

- **Движок**: Yandex SpeechKit
- **Голоса**: Алёна, Филипп, Ермил, Джейн, Омаж, Захар, Марина
- **Формат**: OGG Opus
- **Ключи**: те же `YANDEX_API_KEY` и `YANDEX_FOLDER_ID`, что для Yandex GPT

**Требования Yandex Cloud:**
1. Включить **SpeechKit** в каталоге
2. Сервисный аккаунт с ролью `speechkit.speaker`

**Ограничения:**
- Озвучивается до 5000 символов (настраивается: `/setconfig tts_max_chars 3000`)
- Платный сервис (~1₽ за 1000 символов)

---

## Ollama (локальная модель)

Используйте `/model ollama` для запросов к локально запущенному Ollama (без внешних API).

**Рекомендуемые модели под слабый CPU:**

```bash
ollama pull gemma2:2b-instruct-q4_K_M    # Быстро и стабильно (рекомендуется)
ollama pull qwen2.5:3b-instruct-q4_K_M   # Лучше качество, медленнее
ollama pull qwen2.5:1.5b-instruct-q4_K_M # Если предыдущие слишком медленные
```

Настройки тайм-аута и длины ответа — в `.env` или через `/setconfig`.

---

## Администрирование

Бот имеет Telegram-нативную систему администрирования. Доступ — через `/admin`.

### Первичная настройка

1. Добавьте свой Telegram ID в `.env`:
   ```env
   ADMIN_TELEGRAM_IDS=123456789
   ```
   Несколько администраторов — через запятую.

2. Перезапустите бота — при следующем обращении вы получите роль `admin` автоматически.

### Роли пользователей

| Роль | Вес | Возможности |
|------|-----|-------------|
| `user` | 0 | Базовый доступ к AI-функциям |
| `moderator` | 50 | Команды `/ban`, `/unban` |
| `admin` | 100 | Полный доступ: роли, конфиг, лимиты, статистика |

### Команды администрирования

| Команда | Роль | Описание |
|---------|------|----------|
| `/admin` | admin | Открыть inline-меню администрирования |
| `/ban <telegram_id>` | moderator+ | Заблокировать пользователя |
| `/unban <telegram_id>` | moderator+ | Разблокировать пользователя |
| `/setrole <telegram_id> <role>` | admin | Назначить роль (`user`/`moderator`/`admin`) |
| `/setconfig <key> <value>` | admin | Изменить параметр конфигурации |
| `/setlimit <telegram_id> tokens <N>` | admin | Установить лимит токенов |
| `/setlimit <telegram_id> requests <N>` | admin | Установить лимит запросов |
| `/resetlimits <telegram_id>` | admin | Сбросить суточные счётчики |
| `/usage` | admin | Отчёт об использовании за сегодня |
| `/usage <telegram_id>` | admin | Отчёт по конкретному пользователю за 7 дней |

### Inline-меню (`/admin`)

```
🔐 Админ-панель
├── 👥 Пользователи  — список, поиск, карточка
│   ├── Изменить роль
│   ├── Заблокировать / Разблокировать
│   └── Сбросить лимиты
├── ⚙️ Конфигурация  — просмотр/редактирование по категориям
│   └── (models, limits, tts, system, messages)
├── 📊 Статистика    — запросы, токены, стоимость, по провайдерам
└── 🔧 Система       — Python, БД, uptime, maintenance mode
```

### Динамическая конфигурация

Параметры хранятся в SQLite (`config`) и применяются **без перезапуска** бота.

Приоритет: **БД** > **переменная окружения** > **встроенное значение по умолчанию**.

Пример:
```
/setconfig tts_max_chars 3000
/setconfig maintenance_mode true
/setconfig openai_model gpt-4o
```

### Лимиты использования AI

Суточные лимиты (скользящее окно 24 ч):
- `daily_token_limit` — максимум токенов (по умолчанию 50 000)
- `daily_request_limit` — максимум запросов (по умолчанию 100)

Установить индивидуально:
```
/setlimit 123456789 tokens 5000
/setlimit 123456789 requests 20
/resetlimits 123456789
```

### Учёт стоимости

- **OpenAI и OpenRouter**: реальные токены из API → точный `cost_usd`
- **GigaChat, Yandex GPT, Ollama**: оценочные токены (chars/4), стоимость = 0
- Вся статистика — в таблице `usage_logs` (SQLite), доступна через `/usage` и `/admin` → Статистика

### Maintenance Mode

Включение — через меню `🔧 Система` или командой:
```
/setconfig maintenance_mode true
```
Администраторы продолжают работать, обычные пользователи получают уведомление об обслуживании.

---

## Запуск через systemd

### Установка

```bash
sudo cp blabber.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blabber
sudo systemctl start blabber
```

Или автоматически:
```bash
sudo ./install_service.sh
```

### Управление

```bash
sudo systemctl start blabber      # Запустить
sudo systemctl stop blabber       # Остановить
sudo systemctl restart blabber    # Перезапустить
sudo systemctl status blabber     # Статус

sudo journalctl -u blabber -f     # Логи в реальном времени
sudo journalctl -u blabber -n 50  # Последние 50 строк
```

---

## Структура проекта

```
blabber/
├── bot.py                       # Точка входа, регистрация хендлеров
├── utils.py                     # get_chat_response() — маршрутизация по провайдерам
├── user_storage.py              # In-memory настройки пользователей (модель, голос)
├── tts.py                       # Озвучка через Yandex SpeechKit (OGG Opus)
├── telemetry.py                 # Структурированное логирование (Better Stack)
├── get_token_gch.py             # Получение токена GigaChat API
├── llm_providers/               # Провайдеры LLM
│   ├── openrouter.py            # DeepSeek Chat + DeepSeek R1
│   ├── openai.py                # GPT-4o, GPT-4o-mini
│   ├── gigachat.py              # GigaChat
│   ├── gigachat_token.py        # Кэш токена GigaChat
│   ├── yandexgpt.py             # Yandex GPT (Yandex Cloud ML SDK)
│   └── ollama.py                # Локальная модель (HTTP API)
├── database/                    # Слой SQLite
│   ├── engine.py                # Подключение, WAL, PRAGMA, автомиграции
│   └── migrations/
│       ├── 001_initial.sql      # roles, users, config, usage_logs
│       ├── 002_config_seed.sql  # Начальные параметры конфигурации
│       ├── 003_openai.sql       # openai_model в config
│       └── 004_context.sql      # context_mode в users, context_messages, context_summary
├── repositories/                # CRUD (Data Access Layer)
│   ├── user_repo.py
│   ├── config_repo.py
│   ├── usage_repo.py
│   └── context_repo.py          # CRUD для контекста диалога
├── services/                    # Бизнес-логика
│   ├── user_service.py          # get_or_create, ban, unban, set_role
│   ├── config_registry.py       # Singleton-кеш конфигурации с TTL
│   ├── limiter.py               # Суточные лимиты токенов/запросов
│   ├── usage_service.py         # Логирование LLM-вызовов, отчёты
│   └── context_service.py       # Скользящее окно + summary + TTL контекста
├── middleware/                  # Декораторы хендлеров
│   ├── auth.py                  # @require_role, @with_user_check
│   └── rate_limit.py            # Rate limiting admin-команд (10/мин)
├── handlers/
│   └── admin_commands.py        # Inline-меню и команды администрирования
├── tests/                       # Тестовая сюита (pytest)
│   ├── conftest.py
│   ├── test_user_repo.py
│   ├── test_config_repo.py
│   ├── test_config_registry.py
│   ├── test_limiter.py
│   ├── test_auth.py
│   ├── test_admin_commands.py
│   └── test_user_flow.py
├── blabber.db                   # SQLite-база (создаётся автоматически)
├── env.example                  # Пример переменных окружения
├── requirements.txt
├── requirements-dev.txt         # ruff, pytest
├── pyproject.toml               # Конфиг ruff
├── blabber.service              # Systemd service
├── install_service.sh           # Скрипт установки systemd service
├── TESTING_MANUAL.md            # Руководство по ручному тестированию
├── ADMIN_ROADMAP.md             # Дорожная карта развития
└── README.md
```

---

## Настройка моделей

### GigaChat

1. Получите ключи на [GigaChat Developers](https://developers.sber.ru/gigachat)
2. Добавьте в `.env`:
   ```env
   GIGACHAT_CREDENTIALS=client_id:client_secret
   GIGACHAT_VERIFY_SSL=false
   ```

### OpenRouter (DeepSeek Chat и DeepSeek R1)

1. Получите API ключ на [proxyapi.ru](https://proxyapi.ru/openrouter)
2. Добавьте в `.env`:
   ```env
   PROXY_API_KEY=your_proxy_api_key_here
   ```
3. Один ключ на обе модели: `/model openrouter` и `/model reasoning`

### OpenAI

1. Получите API ключ на [platform.openai.com](https://platform.openai.com/api-keys)
2. Добавьте в `.env`:
   ```env
   OPENAI_API_KEY=sk-your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini  # или gpt-4o, gpt-4-turbo
   ```

### Yandex GPT

1. Создайте каталог в [Yandex Cloud](https://cloud.yandex.ru/)
2. Сервисный аккаунт с ролью `ai.languageModels.user`
3. Добавьте в `.env`:
   ```env
   YANDEX_API_KEY=your_yandex_api_key_here
   YANDEX_FOLDER_ID=your_yandex_folder_id_here
   YANDEX_MODEL=yandexgpt
   ```

---

## Решение проблем

### Ошибки при работе с моделями

- **GigaChat**: формат `GIGACHAT_CREDENTIALS` — `client_id:client_secret`
- **OpenRouter / DeepSeek R1**: один `PROXY_API_KEY` на обе модели
- **OpenAI**: проверьте ключ и баланс аккаунта
- **Yandex GPT**: сервисный аккаунт должен иметь роль `ai.languageModels.user`, Yandex GPT API активирован в каталоге
- **Ollama**: убедитесь, что Ollama запущена и модель скачана (`ollama list`)

### Проблемы с контекстом

| Симптом | Причина |
|---------|---------|
| Бот не помнит реплики | Активен режим вопрос-ответ — выполни `/mode chat` |
| История очистилась сама | TTL 60 мин — долго не писал, контекст сброшен автоматически |
| Ошибка при `/mode` | Не применилась миграция 004 — проверь `PRAGMA table_info(users)` |

### Проверка работы

```bash
sudo systemctl status blabber
sudo journalctl -u blabber -n 50
```

---

## Тестирование

### Автотесты (pytest)

```bash
source venv/bin/activate
pytest tests/ -v
```

101 тест: репозитории, сервисы, auth middleware, лимиты, user flow.

### Ручное тестирование

Подробное руководство по ручному тестированию всех сценариев — в файле [TESTING_MANUAL.md](TESTING_MANUAL.md).

---

## Качество кода

```bash
pip install -r requirements-dev.txt

ruff check .    # Линтинг
ruff format .   # Форматирование
```

---

## Лицензия

Этот проект распространяется без лицензии. Используйте на свой страх и риск.
