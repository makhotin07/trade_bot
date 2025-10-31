#!/bin/bash
# Скрипт для инициализации git репозитория на сервере
# Использование: ./scripts/init_git_on_server.sh

set -e

echo "🔧 Инициализация git репозитория на сервере..."

# Параметры сервера
SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-91.229.8.171}"
SERVER_PATH="${SERVER_PATH:-/root/trade_bot}"

echo "📡 Подключение к серверу: ${SERVER_USER}@${SERVER_HOST}"
echo "📁 Путь на сервере: ${SERVER_PATH}"

ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_HOST} << EOF
    set -e
    
    echo "🔄 Переход в директорию проекта..."
    cd ${SERVER_PATH} || {
        echo "❌ Ошибка: директория ${SERVER_PATH} не найдена"
        exit 1
    }
    
    echo "📋 Проверка текущего состояния git..."
    if [ -d ".git" ]; then
        echo "⚠️  Git репозиторий уже существует"
        echo "📋 Текущий remote:"
        git remote -v || echo "Remote не настроен"
    else
        echo "🔄 Инициализация git репозитория..."
        git init
        git branch -M master
        
        echo "📡 Добавление remote origin..."
        git remote add origin https://github.com/makhotin07/trade_bot.git
        
        echo "✅ Git репозиторий инициализирован"
    fi
    
    echo ""
    echo "🔄 Получение кода из GitHub..."
    git fetch origin master || {
        echo "⚠️  Не удалось получить данные из GitHub"
        echo "Пробуем установить upstream..."
        git branch --set-upstream-to=origin/master master || true
    }
    
    echo "🔄 Обновление кода..."
    git pull origin master || {
        echo "⚠️  Git pull не удался, пробуем reset..."
        git reset --hard origin/master || {
            echo "❌ Не удалось обновить код. Возможно, нужно сначала добавить файлы:"
            echo "   git add ."
            echo "   git commit -m 'Initial commit'"
            exit 1
        }
    }
    
    echo ""
    echo "✅ Код успешно обновлен"
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
    echo "✅ Инициализация завершена успешно"
EOF

echo ""
echo "✅ Инициализация git на сервере завершена"

