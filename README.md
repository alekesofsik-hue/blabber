# Blabber - Telegram-бот "Балабол"

Telegram-бот, который выполняет роль "балабола" — много говорит, любит трепаться и болтать, но не всегда прав и может давать пустую болтовню. Бот поддерживает три модели для генерации текста: GigaChat, OpenRouter (DeepSeek) и Yandex GPT.

## Возможности

- ✅ Поддержка трех моделей: GigaChat, OpenRouter (DeepSeek), Yandex GPT
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
   ```

## Запуск

### Ручной запуск

```bash
# Если виртуальное окружение не активировано
venv/bin/python bot.py

# Или если виртуальное окружение активировано
python bot.py
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
├── env.example         # Пример файла с переменными окружения
├── requirements.txt    # Зависимости проекта
├── blabber.service     # Systemd service файл для автоматического запуска
├── install_service.sh  # Скрипт для установки systemd service
├── README.md           # Документация проекта
└── .gitignore          # Игнорируемые файлы для git
```

### Описание файлов

- **`bot.py`** — основной файл бота, обрабатывает команды и сообщения Telegram
- **`utils.py`** — функции для работы с тремя моделями (GigaChat, OpenRouter, Yandex GPT)
- **`user_storage.py`** — простое хранилище выбора модели для каждого пользователя (в памяти)
- **`get_token_gch.py`** — универсальный модуль для получения токена доступа GigaChat API
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
