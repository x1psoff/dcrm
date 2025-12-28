#!/bin/bash
# Скрипт для удаления systemd службы DCRM

set -e

SYSTEMD_DIR="/etc/systemd/system"
SERVICE_FILE="$SYSTEMD_DIR/dcrm.service"

echo "=========================================="
echo "DCRM Systemd Service Uninstaller"
echo "=========================================="
echo ""

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
   exit 1
fi

# Проверка существования файла службы
if [[ ! -f "$SERVICE_FILE" ]]; then
    echo "⚠️  Служба не установлена"
    exit 0
fi

echo "⏸️  Остановка службы..."
systemctl stop dcrm.service 2>/dev/null || true

echo "❌ Отключение автозапуска..."
systemctl disable dcrm.service 2>/dev/null || true

echo "🗑️  Удаление файла службы..."
rm -f "$SERVICE_FILE"

echo "🔄 Перезагрузка systemd daemon..."
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ Удаление завершено успешно!"
echo "=========================================="
echo ""

