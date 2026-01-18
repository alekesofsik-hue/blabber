# Blabber - Telegram-бот "Балабол"

Telegram-бот, который выполняет роль "балабола" — много говорит, любит трепаться и болтать, но не всегда прав и может давать пустую болтовню. Бот поддерживает несколько моделей для генерации текста: OpenRouter (DeepSeek), GigaChat, Yandex GPT и локальную Ollama.

## Возможности

- ✅ Поддержка моделей: OpenRouter (DeepSeek), GigaChat, Yandex GPT, Ollama (local)
- ✅ Переключение между моделями по команде
- ✅ Системное сообщение задаёт стиль "балабола"
- ✅ Обработка только текстовых сообщений
- ✅ История сообщений не сохраняется — каждый запрос независимый
- ✅ Обработка ошибок с понятными сообщениями
- ✅ Автоматический запуск через systemd

## Требования

- Python 3.8+
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- API ключи для выбранных моделей:
  - **OpenRouter**: API ключ для прокси OpenRouter (api.proxyapi.ru)
  - **GigaChat**: Ключ авторизации GigaChat (client_id:client_secret)
  - **Yandex GPT**: API ключ и Folder ID из Yandex Cloud
  - **Ollama (local)**: локально установленный Ollama и скачанная модель

## Установка

1. **Клонируйте репозиторий** (если используется git) или создайте проект в папке.

2. **Создайте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   ```

3. **Активируйте виртуальное окружение:**
   ```bash
   source venv/bin/activate  # для Linux/Mac
   # или
   venv\Scripts\activate     # для Windows
   ```

4. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Создайте файл `.env`** на основе `env.example`:
   ```bash
   cp env.example .env
   ```

6. **Отредактируйте файл `.env`** и укажите свои токены:
   ```env
   # Обязательные
   TELEGRAM_TOKEN=your_telegram_bot_token_here
   
   # Для OpenRouter (DeepSeek)
   PROXY_API_KEY=your_proxy_api_key_here
   
   # Для GigaChat (опционально, если используете)
   GIGACHAT_CREDENTIALS=your_gigachat_credentials_here
   GIGACHAT_VERIFY_SSL=false
   
   # Для Yandex GPT (опционально, если используете)
   YANDEX_API_KEY=your_yandex_api_key_here
   YANDEX_FOLDER_ID=your_yandex_folder_id_here
   YANDEX_MODEL=yandexgpt

   # Для Ollama (опционально, если используете локальную модель)
   OLLAMA_BASE_URL=http://127.0.0.1:11434
   OLLAMA_MODEL=gemma2:2b-instruct-q4_K_M
   OLLAMA_TIMEOUT=180
   OLLAMA_NUM_PREDICT=256

  # Better Stack Logs (опционально, если хотите смотреть логи в веб-интерфейсе)
  BETTERSTACK_SOURCE_TOKEN=your_betterstack_source_token_here
  BETTERSTACK_INGEST_HOST=your_betterstack_ingest_host_here
  TELEMETRY_USER_HASH_SALT=change_me
  TELEMETRY_LEVEL=INFO
   ```

## Better Stack Logs (Logtail)

Если хотите видеть логи бота в Better Stack:

- **1) Добавьте переменные в `.env`** (см. пример выше)
- **2) Перезапустите сервис**: `sudo systemctl restart blabber`

Что именно отправляется в логи:

- **Текст сообщений пользователей не отправляется** (только метаданные: длина и хеш).
- Добавляются структурированные поля: `request_id`, `provider`, `duration_ms`, `error_type`, `user_id_hash` и т.п.

### Collector (systemd/journald) — дополнительный слой

Отдельно можно подключить Better Stack Collector, чтобы собирать логи `systemd/journald` сервиса `blabber` (старты/падения/рестарты).
Следуйте официальной инструкции Better Stack по установке Collector на Linux и выберите источник `journald`/`systemd`.

## Ollama (локальная модель)

Если хотите использовать **локальную модель** (без внешних API), установите Ollama и скачайте модель.

Рекомендуемые настройки для слабого CPU (чтобы не ловить таймауты):

- `OLLAMA_TIMEOUT=180` (или выше, если нужно)
- `OLLAMA_NUM_PREDICT=256` — ограничивает длину ответа. Для “балабола” это важно, иначе модель может говорить слишком долго.

Рекомендуемый алгоритм выбора модели под слабый CPU:

- 1) **Быстро и стабильно (рекомендуем для сервера): Gemma-2-2B (Q4_K_M)**:
  - `ollama pull gemma2:2b-instruct-q4_K_M`
- 2) Если хочется лучше качество и терпима скорость: **Qwen2.5-3B-Instruct (Q4_K_M)**:
  - `ollama pull qwen2.5:3b-instruct-q4_K_M`
- 3) Если всё ещё медленно: **Qwen2.5-1.5B (Q4_K_M)**:
  - `ollama pull qwen2.5:1.5b-instruct-q4_K_M`

## Запуск

### Ручной запуск

```bash
# Если виртуальное окружение не активировано
venv/bin/python bot.py

# Или если виртуальное окружение активировано
python bot.py
```

### Запуск через Docker Compose (bot + Ollama)

Вариант “самый удобный”: один контейнер с ботом, второй контейнер с Ollama, общая сеть.

#### 1) Подготовьте `.env`

Создайте `.env` (можно на основе `env.example`) и обязательно укажите:

- `TELEGRAM_TOKEN=...`

Если будете использовать **локальную модель через Ollama**, задайте (рекомендуется):

- `OLLAMA_MODEL=gemma2:2b-instruct-q4_K_M`
- `OLLAMA_TIMEOUT=180`
- `OLLAMA_NUM_PREDICT=256`

> В Docker Compose `OLLAMA_BASE_URL` автоматически будет `http://ollama:11434`.

#### 2) Сборка и запуск

```bash
docker compose up -d --build
```

Проверка логов:

```bash
docker compose logs -f blabber
docker compose logs -f ollama
```

Остановка:

```bash
docker compose down
```

#### 3) Важно про Ollama

При первом запуске `ollama` контейнер автоматически выполнит `ollama pull ${OLLAMA_MODEL}` и это может занять время.
Модель и кэш сохраняются в volume `ollama`.

## Качество кода (lint/format)

Проект использует **ruff** (линтер + форматтер) через `pyproject.toml`.

Установка dev-зависимостей:

```bash
python -m pip install -r requirements-dev.txt
```

Проверка:

```bash
ruff check .
```

Форматирование:

```bash
ruff format .
```

## Публикация образа в Docker Hub

Docker Hub username: **`alekesofsik`**.

### 1) Логин

```bash
docker login
```

### 2) Сборка образа

Из корня проекта:

```bash
docker build -t alekesofsik/blabber:latest .
```

Опционально можно добавить версию:

```bash
docker tag alekesofsik/blabber:latest alekesofsik/blabber:1.0.0
```

### 3) Push

```bash
docker push alekesofsik/blabber:latest
docker push alekesofsik/blabber:1.0.0
```

### Автоматический запуск через systemd

Для автоматического запуска бота при загрузке системы и его перезапуска при сбоях можно использовать systemd service.

#### Установка service

1. **Установите service файл:**
   ```bash
   sudo ./install_service.sh
   ```

   Или вручную:
   ```bash
   sudo cp blabber.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

2. **Включите автозапуск при загрузке системы:**
   ```bash
   sudo systemctl enable blabber
   ```

3. **Запустите бота:**
   ```bash
   sudo systemctl start blabber
   ```

#### Управление ботом

```bash
# Запустить бота
sudo systemctl start blabber

# Остановить бота
sudo systemctl stop blabber

# Перезапустить бота
sudo systemctl restart blabber

# Проверить статус
sudo systemctl status blabber

# Просмотр логов в реальном времени
sudo journalctl -u blabber -f

# Просмотр последних логов
sudo journalctl -u blabber -n 50

# Отключить автозапуск
sudo systemctl disable blabber
```

#### Проверка работы

После запуска проверьте, что бот работает:
```bash
sudo systemctl status blabber
```

Вы должны увидеть `Active: active (running)` если всё работает корректно.

## Использование

После запуска бота отправьте ему команду `/start` для начала работы.

### Команды бота

- `/start` — начать работу с ботом
- `/help` — показать справку по командам
- `/models` — показать список доступных моделей и текущую модель
- `/model <название>` — переключить модель:
  - `/model gigachat` — переключить на GigaChat
  - `/model openrouter` — переключить на OpenRouter (DeepSeek)
  - `/model yandexgpt` — переключить на Yandex GPT
  - `/model ollama` — переключить на Ollama (local)

### Примеры использования

```
/start
/models
/model gigachat
Привет, как дела?
```

После каждого ответа бот автоматически напоминает, что контекст беседы не сохраняется.

## Структура проекта

```
blabber/
├── bot.py              # Основной файл запуска бота
├── utils.py            # Утилиты для работы с API моделей
├── user_storage.py     # Хранилище выбора модели пользователями
├── get_token_gch.py    # Модуль для получения токена GigaChat
├── llm_providers/      # Универсальные провайдеры LLM (OpenRouter/GigaChat/YandexGPT/Ollama)
├── env.example         # Пример файла с переменными окружения
├── requirements.txt    # Зависимости проекта
├── requirements-dev.txt# Dev-зависимости (линтер/форматтер)
├── pyproject.toml      # Конфиг ruff (lint/format)
├── blabber.service     # Systemd service файл для автоматического запуска
├── install_service.sh  # Скрипт для установки systemd service
├── README.md           # Документация проекта
└── .gitignore          # Игнорируемые файлы для git
```

### Описание файлов

- **`bot.py`** — основной файл бота, обрабатывает команды и сообщения Telegram
- **`utils.py`** — единая точка входа `get_chat_response()` (обратная совместимость), внутри использует `llm_providers`
- **`user_storage.py`** — простое хранилище выбора модели для каждого пользователя (в памяти)
- **`get_token_gch.py`** — универсальный модуль для получения токена доступа GigaChat API
- **`pyproject.toml`** — конфигурация линтинга/форматирования (ruff)
- **`requirements-dev.txt`** — dev-зависимости (ruff)
- **`env.example`** — пример файла с переменными окружения
- **`blabber.service`** — конфигурация systemd для автоматического запуска
- **`install_service.sh`** — скрипт для автоматической установки systemd service

## Функционал

### Поддерживаемые модели

1. **GigaChat** — модель от Сбербанка
   - Требуется: `GIGACHAT_CREDENTIALS` (client_id:client_secret или base64)
   - Автоматическое кэширование токена (действует 30 минут)
   - Поддержка отключения проверки SSL сертификатов

2. **OpenRouter (DeepSeek)** — модель через прокси OpenRouter
   - Требуется: `PROXY_API_KEY`
   - Используется по умолчанию

3. **Yandex GPT** — модель от Yandex Cloud
   - Требуется: `YANDEX_API_KEY` и `YANDEX_FOLDER_ID`
   - Использует Yandex Cloud ML SDK
   - Поддерживает модели: `yandexgpt`, `yandexgpt-lite`, `yandexgpt-pro`

### Особенности работы

- ✅ Обработка только текстовых сообщений
- ✅ Системное сообщение задаёт стиль "балабола" для всех моделей
- ✅ История сообщений не сохраняется — каждый запрос независимый
- ✅ Индивидуальный выбор модели для каждого пользователя
- ✅ Обработка ошибок с понятными сообщениями
- ✅ Автоматическое напоминание о том, что контекст не сохраняется

## Настройка моделей

### GigaChat

1. Получите ключи авторизации на [GigaChat Developers](https://developers.sber.ru/gigachat)
2. Добавьте в `.env`:
   ```env
   GIGACHAT_CREDENTIALS=client_id:client_secret
   GIGACHAT_VERIFY_SSL=false  # Отключите только если проблемы с SSL
   ```

### OpenRouter (DeepSeek)

1. Получите API ключ на [proxyapi.ru](https://proxyapi.ru/openrouter)
2. Добавьте в `.env`:
   ```env
   PROXY_API_KEY=your_proxy_api_key_here
   ```

### Yandex GPT

1. Создайте каталог в [Yandex Cloud](https://cloud.yandex.ru/)
2. Создайте сервисный аккаунт с ролью `ai.languageModels.user` или `ai.user`
3. Получите API ключ для сервисного аккаунта
4. Добавьте в `.env`:
   ```env
   YANDEX_API_KEY=your_yandex_api_key_here
   YANDEX_FOLDER_ID=your_yandex_folder_id_here
   YANDEX_MODEL=yandexgpt  # или yandexgpt-lite, yandexgpt-pro
   ```

## Решение проблем

### Ошибки при работе с моделями

- **GigaChat**: Убедитесь, что `GIGACHAT_CREDENTIALS` в правильном формате (client_id:client_secret)
- **OpenRouter**: Проверьте, что `PROXY_API_KEY` корректен
- **Yandex GPT**: Убедитесь, что:
  - `YANDEX_API_KEY` и `YANDEX_FOLDER_ID` указаны правильно
  - Сервисный аккаунт имеет необходимые роли
  - Yandex GPT API активирован в каталоге

### Проверка работы бота

```bash
# Проверить логи
sudo journalctl -u blabber -n 50

# Проверить статус
sudo systemctl status blabber

# Перезапустить при проблемах
sudo systemctl restart blabber
```

## Примечания

- Бот не сохраняет историю диалога. Каждое сообщение обрабатывается независимо от предыдущих.
- Выбор модели хранится в памяти и сбрасывается при перезапуске бота.
- Токен GigaChat кэшируется автоматически и обновляется каждые 30 минут.

## Лицензия

Этот проект распространяется без лицензии. Используйте на свой страх и риск.
