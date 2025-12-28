#!/bin/bash
# Скрипт для установки systemd службы DCRM

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/dcrm.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "=========================================="
echo "DCRM Systemd Service Installer"
echo "=========================================="
echo ""

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
   exit 1
fi

# Проверка существования файла службы
if [[ ! -f "$SERVICE_FILE" ]]; then
    echo "❌ Файл службы не найден: $SERVICE_FILE"
    exit 1
fi

echo "📋 Копирование файла службы в $SYSTEMD_DIR..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/dcrm.service"
chmod 644 "$SYSTEMD_DIR/dcrm.service"

echo "🔄 Перезагрузка systemd daemon..."
systemctl daemon-reload

echo "✅ Включение автозапуска службы..."
systemctl enable dcrm.service

echo ""
echo "=========================================="
echo "✅ Установка завершена успешно!"
echo "=========================================="
echo ""
echo "Доступные команды:"
echo "  sudo systemctl start dcrm      # Запустить службу"
echo "  sudo systemctl stop dcrm       # Остановить службу"
echo "  sudo systemctl restart dcrm    # Перезапустить службу"
echo "  sudo systemctl status dcrm     # Статус службы"
echo "  sudo systemctl disable dcrm    # Отключить автозапуск"
echo "  sudo journalctl -u dcrm -f     # Просмотр логов в реальном времени"
echo ""
echo "Служба будет автоматически запускаться при загрузке системы."
echo ""

# Спросить, запустить ли службу сейчас
read -p "Запустить службу сейчас? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Запуск службы..."
    systemctl start dcrm.service
    sleep 3
    echo ""
    systemctl status dcrm.service --no-pager
fi

