# Blabber — Telegram-бот "Балабол"

Telegram-бот, который выполняет роль "балабола" — много говорит, любит трепаться и болтать, но не всегда прав и может давать пустую болтовню. Бот поддерживает шесть LLM-моделей, два режима диалога (с памятью и без), голосовую озвучку ответов и полноценную Telegram-нативную панель администрирования.

## Возможности

- ✅ **6 LLM-моделей**: OpenRouter (DeepSeek), DeepSeek R1, GigaChat, OpenAI (GPT-4o), Yandex GPT, Ollama (local)
- ✅ **Роли (персоны) бота** (`/role`) — переключение стиля/фокуса (ассистент, разработчик, аналитик и др.)
- ✅ **Режим разговора с памятью** (`/mode chat`) — бот помнит контекст диалога
- ✅ **Режим вопрос-ответ** (`/mode single` / `/mode qa`) — каждый запрос независимый (по умолчанию)
- ✅ **Автопамять (с подтверждением)** (`/memory`) — бот иногда предлагает сохранить полезные факты/предпочтения в профиль
- ✅ **Коллекция смешных фраз** (`/quote`, `/quotes`) — сохраняй лучшие реплики Балабола и ищи их по смыслу (LanceDB + семантический поиск)
- ✅ Переключение между моделями в любой момент, контекст при этом сохраняется
- ✅ Озвучка ответов голосовыми сообщениями (TTS, Yandex SpeechKit)
- ✅ Система администрирования: роли пользователей (user/moderator/admin), лимиты, конфиг, статистика
- ✅ Учёт стоимости запросов: реальные токены для OpenAI/OpenRouter + вывод стоимости в рублях (курс ЦБ РФ) для этих провайдеров
- ✅ **Балабол-новостник** (`/agent`) — агентный режим: поиск по RSS и Hacker News, чтение страницы по URL, сохранение URL в KB и сравнение двух свежих заголовков (`/duel`, инструмент `compare_two_headlines`; схема через LangChain)
- ✅ **История дня** (`/historyday`, `/history`) — исторический факт дня, связанное изображение и ответы по сохраненному контексту из `LanceDB`
- ✅ **PDF-отчёт по разговору** (`/report`) — AI-анализ истории чата и генерация структурированного PDF
- ✅ **Docling-powered KB** — структурированная загрузка документов с fallback на legacy parser, summary artifacts, metadata-aware retrieval и safe rollout через feature flags
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
| `/help` | Справка по командам (в т.ч. `/admin` для администраторов) |
| `/models` | Список доступных моделей |
| `/model <название>` | Переключить модель |
| `/role` | Выбрать роль (персону) бота |
| `/mode` | Показать режим диалога (с памятью / без) |
| `/mode chat` | Включить режим с памятью |
| `/mode single` / `/mode qa` | Включить режим вопрос-ответ |
| `/reset` или `/clear` | Очистить историю разговора |
| `/voice` | Показать статус и настройки озвучки |
| `/voice on` / `/voice off` | Включить / выключить озвучку |
| `/voice alena` / `/voice filipp` | Выбрать голос |
| `/remember <факт>` | Сохранить факт о себе, проекте или задаче; смысловые дубли стараемся не плодить |
| `/prefer <предпочтение>` | Сохранить предпочтение по стилю ответа (как отвечать: формат/ограничения) |
| `/profile` | Просмотр и удаление сохранённых фактов/предпочтений |
| `/memory` | Статус автопамяти (подсказки, что можно сохранить в профиль) |
| `/memory on` / `/memory off` | Включить / выключить автопамять |
| `/kb` | Статус и управление базой знаний (RAG) |
| `/kb on` / `/kb off` | Включить / выключить поиск по документам |
| `/kb clear` | Удалить все документы из базы знаний |
| `/kb url <https://...>` | Загрузить веб-страницу в базу знаний |
| `/kb reindex [all\|doc_id] [embeddings\|summary\|all] [dry-run]` | Переиндексировать уже сохранённые документы: пересчёт embeddings, summary artifacts или полный safe backfill (`doc_id` видно в `/kb`) |
| _(файл в чат)_ | Добавить TXT / PDF / DOC / DOCX / MD в базу знаний |
| `/agent` | Балабол-новостник: статус и быстрый просмотр новостей |
| `/agent on` / `/agent off` | Включить / выключить агентный режим |
| `/agent kb <https://...>` | Сохранить ссылку в KB через agent-поток |
| `/duel` или `/compare_headlines` | Явный запуск сравнения двух свежих заголовков из разных RSS-лент (один вызов `compare_two_headlines`; нужен `/agent on`). Примеры: `/duel`, `/duel habr meduza` |
| `/historyday` или `/history` | Сценарий `История дня`: статус, кнопки и подсказки |
| `/historyday help` / `/historyday status` | Повторно показать карточку сценария |
| `/historyday fact [MM-DD\|YYYY-MM-DD]` | Исторический факт дня |
| `/historyday image [дата\|вопрос]` | Связанное изображение и анализ |
| `/historyday context <вопрос>` | Ответ по сохраненному контексту из `LanceDB` |
| `/historyday memory` | Диагностика памяти сценария |
| `/historyday clear` | Очистить память сценария `История дня` |
| `/admin` | Панель администратора (роли, лимиты, конфиг) — только для пользователей с правами |
| `/quote <фраза>` | Сохранить смешную/интересную фразу Балабола в коллекцию |
| `/quotes` | Случайная фраза из коллекции |
| `/quotes list` | Вся коллекция: по 3 цитаты на страницу, кнопки **🗑 1–3** или `/quotes del id` |
| `/quotes search <запрос>` | Поиск фраз по смыслу (семантический, LanceDB) |
| `/quotes del <id>` | Удалить фразу по **id** из подписи под цитатой в списке |
| `/quotes clear` | Очистить всю коллекцию |
| `/quotes help` | Справка по коллекции |
| `/report` | Сгенерировать PDF-отчёт по текущей истории чата |
| `/report help` | Справка по команде /report |

**Про `/start` и `/help`:** встроенные шаблоны лежат в **`bot_texts/defaults.py`** (одно место для правок в коде). В таблице `config` (категория **messages**) можно переопределить:
- **`welcome_message`** — текст `/start`. **Пустая строка** = брать шаблон из `bot_texts/defaults.py` (HTML). Непустое значение = **обычный текст**, плейсхолдер `{model}`.
- **`help_message`** — текст `/help`. **Пустая строка** = шаблон из `bot_texts/defaults.py` (HTML). Непустое = plain text без разметки.

Редактирование без деплоя: `/admin` → Конфигурация → **messages** или `/setconfig welcome_message …` / `/setconfig help_message …`. Чтобы **сбросить** к шаблону из кода: `/setconfig welcome_message` или `/setconfig help_message` **без текста после ключа** (пустая строка в БД).

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

## Архитектура памяти (три слоя)

Blabber реализует **комбинированную память** — три независимых слоя, которые подмешиваются в каждый запрос к LLM:

```
[System]          ← адаптивная персона «Балабол» + гарды (если есть внешний контекст)
[Профиль]         ← факты + предпочтения из /remember и /prefer  (долгосрочная память D)
[История чата]    ← скользящее окно из /mode chat  (короткая память C)
[Summary]         ← сжатое резюме старых реплик (инжект в system prompt)  (короткая память C)
[База знаний]     ← релевантные фрагменты из документов  (RAG, долгосрочная память C)
[User message]    ← текущий вопрос
```

### Короткая память (`/mode chat`)

- **Вопрос-ответ** (`/mode single` или `/mode qa`) — каждое сообщение обрабатывается независимо. **По умолчанию.**
- **Чат** (`/mode chat`) — бот помнит историю диалога (окно 10 реплик) + хранит сжатое резюме старых реплик.

Переключить можно командой (`/mode chat`, `/mode single`, `/mode qa`) или через меню `/mode`.

При смене модели (`/model ...`) история диалога **не сбрасывается** — контекст общий для всех моделей.

**TTL**: если молчать более 60 минут, история автоматически очищается.

**Очистка**: `/reset` или `/clear` — спросит подтверждение, затем сотрёт историю и резюме.

### Долгосрочная память: профиль пользователя (`/remember`, `/prefer`)

Пункты профиля хранятся в SQLite и инжектируются в **каждый** запрос к LLM, независимо от режима чата:

```
/remember Меня зовут Алексей
/remember Мой проект — Telegram-бот на Python
/remember Я работаю аналитиком данных
/prefer Не использовать эмодзи
/prefer Отвечай кратко и по делу
/profile                          ← посмотреть и удалить сохранённое
```

- Лимит: 20 пунктов, 300 символов каждый
- Сохраняются навсегда (до явного удаления)
- Работают со всеми 6 LLM-моделями
- `/remember` использует семантическую проверку дублей: при очень близкой по смыслу формулировке бот может не создать дубль или обновить существующую запись
- Поведение этой проверки настраивается через `USER_MEMORY_SEMANTIC_ENABLED`, `USER_MEMORY_SIMILARITY_THRESHOLD`, `USER_MEMORY_DECISION_MODE`, `USER_MEMORY_TOP_K`
- `/prefer` хранит предпочтения как отдельные записи без семантической дедупликации

## База знаний: текущий статус rollout

Новая KB-система уже умеет:

- парсить документы через `Docling` с безопасным fallback на legacy parser
- строить structured chunks с metadata (`section`, `table`, `page`, `heading_path`)
- сохранять summary artifacts (`summary`, `key_topics`, `suggested_questions`)
- использовать metadata-aware retrieval для section/table/page запросов
- выполнять safe reindex/backfill без raw-file reparse

Основные operational файлы:

- `KB_OPERATIONS.md` — reindex, logs, backfill, feature flags
- `TESTING_MANUAL.md` — ручные сценарии проверки

Ключевые KB-флаги в `/admin` → `kb`:

- `kb_docling_enabled`
- `kb_docling_fallback_enabled`
- `kb_docling_structured_chunks_enabled`
- `kb_doc_summary_enabled`
- `kb_doc_summary_save_enabled`
- `kb_structured_retrieval_enabled`
- `kb_max_doc_size_kb`

### Автопамять (подсказки, что запомнить)

В режиме `/mode chat` бот может периодически предлагать сохранить **полезные факты и предпочтения**
из диалога. Сохранение происходит **только после подтверждения кнопкой**.
При подтверждении факты проходят через ту же проверку на смысловые дубли, что и ручной `/remember`.

Управление:

```
/memory        # статус
/memory on     # включить
/memory off    # выключить
```

## History Day Feature

В проекте добавлен отдельный сценарий `История дня`, доступный через:

```text
/historyday
/history
```

Сценарии:

- `Fact Of The Day`
- `Related Image And Analysis`
- `Retrieval From Saved Context`

Технически:

- tools-layer новой фичи использует реальный `haystack-ai`
- память сценария хранится в `LanceDB`
- retrieval изолирован от обычного `context_service` и от `/kb`

Команды:

```text
/historyday help
/historyday fact
/historyday image
/historyday context О чем ты мне только что рассказывал?
/historyday memory
/historyday clear
```

Особенности поведения:

- факт дня выбирается только из событий, у которых есть изображение;
- `/historyday image Что на нем показано?` трактуется как вопрос про текущее изображение, а не как дата;
- если памяти недостаточно, бот честно сообщает, что не смог поднять релевантный контекст.

### Долгосрочная память: база знаний (RAG)

Загрузи документ в чат или добавь веб-страницу по URL — бот проиндексирует источник и будет отвечать на вопросы по нему:

```
(пришли файл .txt / .pdf / .docx / .md)
/kb              ← статус и список документов
/kb on / off     ← включить / выключить
/kb clear        ← удалить все документы
/kb url https://example.com/article
/kb reindex all all dry-run
```

**Как работает (гибридный поиск: BM25 + LanceDB):**
1. Текст документа разбивается на фрагменты (~800 символов с перекрытием)
2. Для каждого фрагмента вычисляется embedding (OpenAI `text-embedding-3-small`)
3. При вопросе — гибридный retrieval:
   - **BM25** — быстрый лексический отбор top-10 кандидатов по ключевым словам
   - **LanceDB** — семантические кандидаты из vector store
   - **Итоговый скор** = 0.3 × BM25 + 0.7 × semantic — баланс точности и смысла
4. Топ-3 наиболее релевантных фрагмента инжектируются в запрос к LLM
5. Системный промпт автоматически добавляет «не выдумывай, используй факты из базы»
6. Балабол-персона при этом **сохраняется** — шутит, болтает, но факты не искажает
7. При удалении документа или полной очистке KB бот дополнительно сбрасывает chat-context, чтобы не отвечать по «призрачной» памяти удалённых источников

**Graceful degradation:** если `OPENAI_API_KEY` не задан — embeddings не считаются, поиск работает на BM25-only. Качество ниже, но всё функционирует.

**Rollback:** при необходимости можно временно вернуть legacy retrieval через `.env`:

```env
KB_VECTOR_BACKEND=sqlite
```

Если хочешь освежить rollback buffer для уже сохранённых документов:

```env
KB_WRITE_LEGACY_EMBEDDING=true
```

А затем:

```text
/kb reindex all embeddings
```

По умолчанию используется:

```env
KB_VECTOR_BACKEND=lancedb
KB_ENABLE_DUAL_WRITE=true
KB_ENABLE_URL_INGESTION=true
KB_WRITE_LEGACY_EMBEDDING=false
KB_ENABLE_SHADOW_COMPARE=false
```

**Источники знаний:**
- Файлы: TXT, PDF, DOC, DOCX, MD — основной parser `Docling`, для части сценариев доступен legacy fallback
- Веб-страницы: `/kb url https://...` (HTML/text, публичные URL)

**Лимиты:** 10 документов, размер файла по умолчанию до 3 МБ (`kb_max_doc_size_kb` через `/admin`)

**Хранение:**  
- `SQLite` — документы, тексты чанков, метаданные источника (`file` / `url`)  
- `LanceDB` — primary semantic retrieval backend  
- `kb_chunks.embedding` — optional rollback buffer; новые записи туда по умолчанию больше не пишутся

**Переиндексация:** `/kb reindex [all|<doc_id>] [embeddings|summary|all] [dry-run]` работает по уже сохранённым chunk'ам и metadata. `doc_id` бот показывает в списке `/kb`. Это полезно после изменения KB-флагов, safe backfill и пересборки summary/embeddings без повторной загрузки исходного файла.

**Прозрачность ответа:** если KB включена, бот после ответа явно пишет, использовал ли он базу знаний, и показывает источники.

---

## Коллекция смешных фраз (`/quote`, `/quotes`)

Балабол иногда выдаёт настоящее золото. Теперь это можно сохранить и найти по смыслу.

### Использование

```
/quote Я не баг — я фича с характером!    ← сохранить фразу
/quotes                                    ← случайная фраза
/quotes list                               ← страницы по 3 цитаты + кнопки 🗑 1–3
/quotes search грусть                      ← найти по смыслу (семантический поиск!)
/quotes search ошибки в коде               ← найдёт фразы про баги, даже без слова "баги"
/quotes del 3                              ← удалить фразу с id=3 (как в подписи «id 3»)
/quotes clear                              ← очистить всю коллекцию
/quotes help                               ← справка
```

### Как работает (LanceDB + семантический поиск)

Коллекция использует **двойное хранилище**:

| Хранилище | Данные | Назначение |
|-----------|--------|------------|
| SQLite    | id, текст, дата | Листинг, случайные фразы, удаление |
| LanceDB   | Embedding-вектора (1536 dim) | Семантический поиск по смыслу |

**Как работает семантический поиск:**
1. При сохранении фразы вычисляется её embedding (OpenAI `text-embedding-3-small`)
2. При поиске запрос тоже превращается в вектор
3. LanceDB находит ближайшие по смыслу фразы через ANN-поиск (approximate nearest neighbor)
4. Результат: `/quotes search грусть` найдёт «Оптимизм — это баг, который я пока не починил» — без слова «грусть»!

**Список `/quotes list`:** на странице до **3** полных цитат (лимит одного сообщения Telegram), переносы строк сохраняются; кнопки **🗑 1**, **🗑 2**, **🗑 3** — удалить строку с тем же номером (без дублирования текста в кнопке). Если даже три цитаты с HTML не помещаются (~4096 символов), бот слегка урежет текст на странице и добавит пояснение.

**Вывод результатов поиска:** режим (семантика или подстрока), число фраз в коллекции и сколько показано; для семантики — подсказка по лучшему совпадению, у каждой строки id, дата, условная оценка ~%, метка (🟢/🟡/🟠) и служебная метрика `d≈…` (меньше = ближе; для ориентира, не «вероятность»).

**Graceful degradation:** если `OPENAI_API_KEY` не задан — фразы сохраняются без векторов, `/quotes search` работает через ключевые слова.

**Лимиты:** 500 фраз на пользователя, до 1000 символов каждая.

**Хранение данных:** LanceDB-файлы в `lancedb_data/` рядом с `blabber.db`. Путь можно переопределить через `LANCEDB_PATH` в `.env`; в этом каталоге живут векторные таблицы цитат, KB и semantic memory пользователя.

---

## Балабол-новостник (Agent-режим)

Агент `/agent` превращает бота в новостного ассистента: он сам решает, нужно ли что-то найти, и использует набор инструментов для поиска свежей информации.

### Как работает

1. Пользователь включает агент: `/agent on`
2. Опционально: команда `/duel` (или `/compare_headlines`) — бот подставляет в агент явный запрос вызвать инструмент **compare_two_headlines** (случайные две ленты или два ключа: `/duel habr meduza`), чтобы модель не ушла в два отдельных `top_headlines`.
3. Опционально: `/agent kb https://example.com/article` — агент тем же общим pipeline сохранит страницу в KB.
4. Каждое следующее сообщение обрабатывается агентным циклом:
   - LLM получает системный промпт с описанием доступных инструментов
   - LLM решает, какой инструмент вызвать (или отвечает сразу без поиска)
   - Результат инструмента возвращается в LLM, которая формирует финальный ответ
5. Включить/выключить режим: `/agent on` / `/agent off`

### Инструменты агента

- **RSS-поиск** — Хабр, 3DNews, Лента, Hacker News и другие источники
- **Топ заголовков** — быстрый просмотр последних новостей по источнику
- **Тренды HN** — топ историй Hacker News прямо сейчас
- **Fetch URL** — читает и пересказывает страницу по ссылке
- **Save URL to KB** — сохраняет страницу в персональную базу знаний пользователя
- **compare_two_headlines** — два свежих заголовка из **разных** RSS-лент для шутливого сравнения; схема для LLM собирается через **LangChain** (`@tool` + `convert_to_openai_tool`)

### MCP (опционально)

Если задан `MCP_BASE_URL`, агент использует внешний MCP-сервер вместо встроенных инструментов.

---

## PDF-отчёт по разговору (`/report`)

Команда `/report` анализирует историю текущего чата с помощью LLM и создаёт структурированный PDF-отчёт.

### Как использовать

1. Включить режим чата: `/mode chat`
2. Поговорить с ботом
3. Написать `/report`
4. Получить PDF-файл в чат

### Обложка-картинка

Если задан `OPENAI_API_KEY`, бот дополнительно генерирует простую обложку-картинку по теме разговора и вставляет её в начало отчёта.
Если ключа нет или генерация не удалась — отчёт сформируется без картинки.

### Что войдёт в отчёт

- Тема разговора
- Краткое резюме
- Обложка-картинка по теме (опционально)
- Ключевые тезисы
- Принятые решения
- Открытые вопросы
- Следующие шаги

### Зависимости

```bash
pip install jinja2 weasyprint
```

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
├── bot_texts/                   # Встроенные шаблоны /start и /help (см. defaults.py)
│   └── defaults.py
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
│       ├── 004_context.sql      # context_mode в users, context_messages, context_summary
│       ├── 005_user_profile.sql # user_profiles (память D)
│       ├── 006_knowledge_base.sql # kb_documents, kb_chunks (память C / RAG)
│       ├── 007_kb_embedding.sql # legacy embedding BLOB в kb_chunks (rollback path)
│       ├── 008_persona.sql      # роли/персоны бота
│       ├── 009_auto_memory.sql  # автопамять (подсказки)
│       ├── 010_quotes.sql       # коллекция цитат (метаданные; векторы в LanceDB)
│       ├── 011_messages_help_and_welcome.sql  # help_message; welcome_message пустой = шаблон из кода
│       ├── 012_kb_chunk_uid.sql # stable chunk_uid для связи SQLite ↔ LanceDB
│       ├── 013_kb_url_sources.sql # source_type/source_url для file/url источников KB
│       ├── 014_kb_docling_rollout.sql # feature flags и rollout stage для Docling KB
│       ├── 015_kb_max_doc_size_config.sql # настраиваемый лимит размера файла KB
│       ├── 016_kb_structured_metadata.sql # structured metadata для документов и чанков
│       └── 017_kb_summary_timestamps.sql # статус, timestamp и ошибка генерации summary
├── repositories/                # CRUD (Data Access Layer)
│   ├── user_repo.py
│   ├── config_repo.py
│   ├── usage_repo.py
│   ├── context_repo.py          # CRUD для контекста диалога
│   ├── profile_repo.py          # CRUD для профиля пользователя (память D)
│   ├── knowledge_repo.py        # SQLite metadata/text для базы знаний (память C / RAG)
│   ├── kb_vector_repo.py        # LanceDB vector layer для KB
│   ├── auto_memory_repo.py      # автопамять
│   ├── quotes_repo.py           # коллекция цитат: SQLite + LanceDB
│   └── lancedb_store.py         # общий LanceDB helper
├── services/                    # Бизнес-логика
│   ├── user_service.py          # get_or_create, ban, unban, set_role
│   ├── config_registry.py       # Singleton-кеш конфигурации с TTL
│   ├── limiter.py               # Суточные лимиты токенов/запросов
│   ├── usage_service.py         # Логирование LLM-вызовов, отчёты
│   ├── context_service.py       # Скользящее окно + summary + TTL контекста
│   ├── profile_service.py       # Личные факты пользователя (долгосрочная память D)
│   ├── knowledge_service.py     # RAG: чанкинг, BM25 + LanceDB retrieval, URL/file ingestion
│   ├── docling_service.py       # Docling parser + legacy fallback + PDF sandboxing
│   ├── kb_ingestion_pipeline.py # structured blocks, normalized document, chunk builder
│   ├── document_summary_service.py # summary, topics, suggested questions
│   ├── kb_upload_feedback.py    # Telegram HTML для результата загрузки документа
│   ├── kb_answer_transparency.py # footer о том, использована ли KB в ответе
│   ├── kb_rollout.py            # feature flags, rollout policy, structured logging
│   ├── embedding_service.py     # OpenAI embeddings, cosine similarity, BLOB сериализация
│   ├── url_ingestion_service.py # загрузка и очистка веб-страниц для KB
│   ├── auto_memory_service.py   # автопамять
│   ├── quotes_service.py        # коллекция цитат, семантический поиск
│   ├── agent_tools.py           # Инструменты агента: RSS, HN, fetch URL, compare_two_headlines (LangChain)
│   ├── agent_runner.py          # Цикл агента: LLM → tool call → LLM
│   ├── mcp_client.py            # MCP-клиент (опциональный внешний сервер инструментов)
│   └── report_service.py        # PDF-отчёт: анализ истории чата через LLM → Jinja2 → WeasyPrint
├── middleware/                  # Декораторы хендлеров
│   ├── auth.py                  # @require_role, @with_user_check
│   └── rate_limit.py            # Rate limiting admin-команд (10/мин)
├── handlers/
│   ├── admin_commands.py        # Inline-меню и команды администрирования
│   ├── profile_commands.py      # /remember, /prefer, /profile (память D)
│   ├── knowledge_commands.py    # /kb, загрузка документов (память C / RAG)
│   ├── persona_commands.py      # /role — выбор роли (персоны) бота
│   ├── agent_commands.py        # /agent — Балабол-новостник (агентный режим)
│   ├── quote_commands.py        # /quote, /quotes — коллекция цитат
│   └── report_commands.py       # /report — генерация PDF-отчёта по истории чата
├── templates/
│   └── report_template.html     # Jinja2-шаблон PDF-отчёта
├── reports/                     # Сгенерированные PDF-файлы (создаётся автоматически)
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

244 теста: репозитории, сервисы, auth middleware, KB rollout/reindex/docling, history day, лимиты, user flow, шаблоны `bot_texts`.

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
