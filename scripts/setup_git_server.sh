#!/bin/bash
# Скрипт для настройки git на сервере вручную
# Запустите этот скрипт НА СЕРВЕРЕ

set -e

SERVER_PATH="/root/trade_bot"

echo "🔧 Настройка git репозитория на сервере..."

cd "$SERVER_PATH" || {
    echo "❌ Директория $SERVER_PATH не найдена"
    exit 1
}

echo "📋 Проверка текущего состояния git..."
if [ -d ".git" ]; then
    echo "⚠️  Git репозиторий уже существует"
    git remote -v || echo "Remote не настроен"
else
    echo "🔄 Инициализация git репозитория..."
    git init
    git branch -M master
    echo "✅ Git репозиторий инициализирован"
fi

echo "📡 Настройка remote origin..."
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/makhotin07/trade_bot.git

echo ""
echo "🔄 Получение кода из GitHub..."
git fetch origin master || {
    echo "⚠️  Fetch не удался, возможно репозиторий пустой"
}

echo "🔄 Обновление кода..."
if git pull origin master 2>/dev/null; then
    echo "✅ Код успешно обновлен"
else
    echo "⚠️  Pull не удался, пробуем reset..."
    git reset --hard origin/master || {
        echo "❌ Не удалось обновить код"
        echo "Попробуйте выполнить вручную:"
        echo "  git fetch origin master"
        echo "  git reset --hard origin/master"
        exit 1
    }
fi

echo ""
echo "✅ Git настроен успешно!"
echo "📋 Текущий коммит:"
git log --oneline -1

echo ""
echo "📦 Обновление зависимостей..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r requirements.txt --upgrade --quiet
    echo "✅ Зависимости обновлены"
else
    echo "⚠️  Виртуальное окружение не найдено"
fi

echo ""
echo "🔄 Перезапуск бота..."
if systemctl is-active --quiet bytbit-bot.service 2>/dev/null; then
    systemctl restart bytbit-bot.service
    echo "✅ Бот перезапущен"
else
    echo "⚠️  Сервис bytbit-bot.service не запущен"
fi

echo ""
echo "✅ Настройка завершена успешно!"

