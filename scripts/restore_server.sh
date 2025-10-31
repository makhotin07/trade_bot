#!/bin/bash
# Скрипт для восстановления проекта на сервере
# Запустите этот скрипт НА СЕРВЕРЕ

set -e

SERVER_PATH="/root/trade_bot"

echo "🔧 Восстановление проекта на сервере..."

cd /root || {
    echo "❌ Не удалось перейти в /root"
    exit 1
}

# Если директория существует, проверяем что в ней
if [ -d "$SERVER_PATH" ]; then
    echo "📋 Проверка содержимого директории..."
    ls -la "$SERVER_PATH" || echo "⚠️  Директория пуста или повреждена"
    
    cd "$SERVER_PATH"
    
    # Если есть .git, пробуем восстановить
    if [ -d ".git" ]; then
        echo "✅ Git репозиторий найден, пробуем восстановить..."
        git fetch origin master || true
        git reset --hard origin/master || true
    else
        echo "⚠️  Git репозиторий не найден, клонируем заново..."
        cd /root
        rm -rf "$SERVER_PATH" 2>/dev/null || true
        git clone https://github.com/makhotin07/trade_bot.git
        cd "$SERVER_PATH"
    fi
else
    echo "🔄 Директория не найдена, клонируем проект..."
    git clone https://github.com/makhotin07/trade_bot.git
    cd "$SERVER_PATH"
fi

echo ""
echo "📦 Восстановление виртуального окружения и зависимостей..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Виртуальное окружение создано"
fi

source .venv/bin/activate
pip install -r requirements.txt --upgrade --quiet

echo ""
echo "📁 Создание необходимых директорий..."
mkdir -p src/bytbit_trading_bot/data
touch src/bytbit_trading_bot/data/users.json
touch src/bytbit_trading_bot/data/tokens.json

# Если файлы пустые, добавляем пустые JSON объекты
if [ ! -s src/bytbit_trading_bot/data/users.json ]; then
    echo "{}" > src/bytbit_trading_bot/data/users.json
fi
if [ ! -s src/bytbit_trading_bot/data/tokens.json ]; then
    echo "{}" > src/bytbit_trading_bot/data/tokens.json
fi

echo ""
echo "🔄 Проверка systemd сервиса..."
if [ -f "scripts/bytbit-bot.service" ]; then
    cp scripts/bytbit-bot.service /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload 2>/dev/null || true
    echo "✅ Systemd сервис обновлен"
fi

echo ""
echo "✅ Восстановление завершено!"
echo "📋 Текущий коммит:"
git log --oneline -1 || echo "⚠️  Не удалось получить коммит"

echo ""
echo "📋 Содержимое директории:"
ls -la

echo ""
echo "🔄 Перезапуск бота..."
if systemctl is-active --quiet bytbit-bot.service 2>/dev/null; then
    systemctl restart bytbit-bot.service
    echo "✅ Бот перезапущен"
    systemctl status bytbit-bot.service --no-pager || true
else
    echo "⚠️  Сервис не запущен. Запустите вручную:"
    echo "   systemctl start bytbit-bot.service"
fi

