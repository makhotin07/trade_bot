#!/bin/bash
# Скрипт для быстрого развертывания через SSH

set -e

SERVER="root@91.229.8.171"
PROJECT_DIR="/root/trade_bot"
REPO_URL="https://github.com/makhotin07/trade_bot.git"

echo "🚀 Развертывание проекта на сервер..."

# Проверка подключения
echo "🔌 Проверка подключения к серверу..."
ssh -o ConnectTimeout=5 "$SERVER" "echo 'Подключение успешно!'" || {
    echo "❌ Не удалось подключиться к серверу"
    exit 1
}

# Загрузка скрипта развертывания на сервер
echo "📤 Загрузка скрипта развертывания..."
scp scripts/deploy.sh "$SERVER:/tmp/deploy.sh"

# Выполнение скрипта на сервере
echo "⚙️  Выполнение развертывания на сервере..."
ssh "$SERVER" "chmod +x /tmp/deploy.sh && /tmp/deploy.sh"

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📝 Для подключения к серверу:"
echo "   ssh $SERVER"
echo ""
echo "📝 Для запуска бота:"
echo "   ssh $SERVER 'cd $PROJECT_DIR && source .venv/bin/activate && python main.py'"

