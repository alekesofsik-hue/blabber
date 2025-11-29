#!/bin/bash
# Скрипт для установки systemd service для Blabber бота

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="blabber.service"
SYSTEMD_DIR="/etc/systemd/system"
# Определяем реального пользователя как владельца директории проекта
CURRENT_USER=$(stat -c '%U' "$SCRIPT_DIR" 2>/dev/null || stat -f '%Su' "$SCRIPT_DIR" 2>/dev/null || echo "$SUDO_USER")

echo "Установка systemd service для Blabber бота..."
echo "Директория проекта: $SCRIPT_DIR"
echo "Пользователь: $CURRENT_USER"

# Проверяем, что скрипт запущен от root или с sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Ошибка: этот скрипт должен быть запущен с правами root (используйте sudo)"
    exit 1
fi

# Проверяем существование файлов
if [ ! -f "$SCRIPT_DIR/$SERVICE_FILE" ]; then
    echo "Ошибка: файл $SERVICE_FILE не найден в $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/bot.py" ]; then
    echo "Ошибка: файл bot.py не найден в $SCRIPT_DIR"
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Ошибка: виртуальное окружение venv не найдено в $SCRIPT_DIR"
    echo "Пожалуйста, сначала создайте виртуальное окружение: python3 -m venv venv"
    exit 1
fi

# Создаём временный файл service с обновлёнными путями
TEMP_SERVICE=$(mktemp)
sed "s|/home/ezovskikh_a/apps/blabber|$SCRIPT_DIR|g; s|User=ezovskikh_a|User=$CURRENT_USER|g" "$SCRIPT_DIR/$SERVICE_FILE" > "$TEMP_SERVICE"

# Копируем service файл в systemd
cp "$TEMP_SERVICE" "$SYSTEMD_DIR/$SERVICE_FILE"
rm "$TEMP_SERVICE"

# Перезагружаем systemd
systemctl daemon-reload

echo ""
echo "✓ Service файл установлен: $SYSTEMD_DIR/$SERVICE_FILE"
echo ""
echo "Для управления ботом используйте следующие команды:"
echo "  sudo systemctl start blabber      - запустить бота"
echo "  sudo systemctl stop blabber       - остановить бота"
echo "  sudo systemctl restart blabber    - перезапустить бота"
echo "  sudo systemctl enable blabber     - включить автозапуск при загрузке"
echo "  sudo systemctl disable blabber    - отключить автозапуск"
echo "  sudo systemctl status blabber     - статус бота"
echo "  sudo journalctl -u blabber -f     - просмотр логов в реальном времени"

