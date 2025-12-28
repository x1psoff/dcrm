#!/bin/bash
# Скрипт для проверки systemd службы без установки

echo "=========================================="
echo "🔍 DCRM Systemd Service Check"
echo "=========================================="
echo ""

SERVICE_FILE="$(dirname "$0")/dcrm.service"

if [[ ! -f "$SERVICE_FILE" ]]; then
    echo "❌ Файл службы не найден: $SERVICE_FILE"
    exit 1
fi

echo "✅ Файл службы найден: $SERVICE_FILE"
echo ""
echo "📋 Содержимое службы:"
echo "=========================================="
cat "$SERVICE_FILE"
echo "=========================================="
echo ""

echo "🔍 Проверка синтаксиса systemd..."
systemd-analyze verify "$SERVICE_FILE" 2>&1 | head -20

echo ""
echo "✅ Проверка завершена!"
echo ""
echo "Для установки службы выполните:"
echo "  sudo ./install.sh"
echo ""

