#!/bin/bash
# Скрипт для установки systemd services для Blabber (бот + MCP сервер)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="/etc/systemd/system"
CURRENT_USER=$(stat -c '%U' "$SCRIPT_DIR" 2>/dev/null || stat -f '%Su' "$SCRIPT_DIR" 2>/dev/null || echo "$SUDO_USER")

echo "Установка systemd services для Blabber..."
echo "Директория проекта: $SCRIPT_DIR"
echo "Пользователь: $CURRENT_USER"

if [ "$EUID" -ne 0 ]; then
    echo "Ошибка: этот скрипт должен быть запущен с правами root (используйте sudo)"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/blabber.service" ]; then
    echo "Ошибка: файл blabber.service не найден в $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/bot.py" ]; then
    echo "Ошибка: файл bot.py не найден в $SCRIPT_DIR"
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Ошибка: виртуальное окружение venv не найдено в $SCRIPT_DIR"
    echo "Пожалуйста, создайте: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

_install_service() {
    local SERVICE_FILE=$1
    local TEMP_SERVICE
    TEMP_SERVICE=$(mktemp)
    sed "s|/home/ezovskikh_a/apps/blabber|$SCRIPT_DIR|g; s|User=ezovskikh_a|User=$CURRENT_USER|g" "$SCRIPT_DIR/$SERVICE_FILE" > "$TEMP_SERVICE"
    cp "$TEMP_SERVICE" "$SYSTEMD_DIR/$SERVICE_FILE"
    rm "$TEMP_SERVICE"
    echo "  ✓ $SERVICE_FILE"
}

# Устанавливаем blabber.service (бот)
_install_service "blabber.service"

# Устанавливаем blabber-mcp.service (MCP сервер), если есть
if [ -f "$SCRIPT_DIR/blabber-mcp.service" ]; then
    if [ ! -d "$SCRIPT_DIR/mcp_server" ]; then
        echo "Предупреждение: mcp_server/ не найден, blabber-mcp.service может не заработать."
    fi
    _install_service "blabber-mcp.service"
    echo ""
    echo "Перед первым запуском MCP установи зависимости: pip install -r mcp_server/requirements.txt"
fi

systemctl daemon-reload

echo ""
echo "✓ Services установлены в $SYSTEMD_DIR"
echo ""
echo "Бот:"
echo "  sudo systemctl start blabber      - запустить"
echo "  sudo systemctl stop blabber       - остановить"
echo "  sudo systemctl enable blabber     - автозапуск при загрузке"
echo "  sudo systemctl status blabber     - статус"
echo "  sudo journalctl -u blabber -f     - логи"
echo ""
if [ -f "$SCRIPT_DIR/blabber-mcp.service" ]; then
    echo "MCP сервер (инструменты агента):"
    echo "  sudo systemctl start blabber-mcp   - запустить"
    echo "  sudo systemctl stop blabber-mcp    - остановить"
    echo "  sudo systemctl enable blabber-mcp  - автозапуск при загрузке"
    echo "  sudo systemctl status blabber-mcp  - статус"
    echo "  sudo journalctl -u blabber-mcp -f  - логи"
    echo ""
fi

