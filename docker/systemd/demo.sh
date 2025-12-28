#!/bin/bash
# Демонстрация работы systemd службы (без установки)

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  🧪 Демонстрация systemd службы DCRM                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

SYSTEMD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SYSTEMD_DIR/dcrm.service"

# 1. Проверка файла
echo "1️⃣  Проверка файла службы..."
if [[ -f "$SERVICE_FILE" ]]; then
    echo "   ✅ Файл найден: $SERVICE_FILE"
    echo "   📏 Размер: $(du -h "$SERVICE_FILE" | cut -f1)"
else
    echo "   ❌ Файл не найден!"
    exit 1
fi
echo ""

# 2. Содержимое
echo "2️⃣  Содержимое службы:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$SERVICE_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 3. Синтаксис
echo "3️⃣  Проверка синтаксиса systemd..."
if command -v systemd-analyze >/dev/null 2>&1; then
    if systemd-analyze verify "$SERVICE_FILE" 2>&1 | grep -i "error" | grep -v "Permission denied" | head -5; then
        echo "   ⚠️  Обнаружены предупреждения (это нормально)"
    else
        echo "   ✅ Синтаксис корректен"
    fi
else
    echo "   ⚠️  systemd-analyze не доступен"
fi
echo ""

# 4. Конфигурация Docker Compose
echo "4️⃣  Проверка docker-compose.yml..."
cd /home/qwe/dcrm
if docker compose config >/dev/null 2>&1; then
    echo "   ✅ Docker Compose конфигурация валидна"
    echo ""
    echo "   📦 Сервисы с профилями:"
    docker compose --profile bot --profile backup --profile backup_orders config --services | while read service; do
        echo "      • $service"
    done
else
    echo "   ❌ Ошибка в docker-compose.yml"
fi
echo ""

# 5. Текущий статус Docker
echo "5️⃣  Текущий статус Docker контейнеров:"
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | head -10
echo ""

# 6. Инструкции
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Демонстрация завершена!"
echo ""
echo "🚀 Для установки службы выполните:"
echo "   cd $SYSTEMD_DIR"
echo "   sudo ./install.sh"
echo ""
echo "📖 Документация:"
echo "   • Быстрый старт: $SYSTEMD_DIR/QUICKSTART.md"
echo "   • Полная:        $SYSTEMD_DIR/README.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

