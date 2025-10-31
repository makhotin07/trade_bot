#!/bin/bash
# Скрипт для ручного деплоя на сервер
# Использование: ./scripts/deploy_manual.sh

set -e

echo "🚀 Начало ручного деплоя..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверяем, что мы в правильной директории
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Ошибка: файл main.py не найден. Запустите скрипт из корня проекта.${NC}"
    exit 1
fi

# Параметры сервера (можно переопределить через переменные окружения)
SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-91.229.8.171}"
SERVER_PATH="${SERVER_PATH:-/root/trade_bot}"

echo -e "${YELLOW}📡 Подключение к серверу: ${SERVER_USER}@${SERVER_HOST}${NC}"
echo -e "${YELLOW}📁 Путь на сервере: ${SERVER_PATH}${NC}"

# SSH команда для деплоя
ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_HOST} << EOF
    set -e
    
    echo "🔄 Переход в директорию проекта..."
    cd ${SERVER_PATH} || {
        echo -e "${RED}❌ Ошибка: директория ${SERVER_PATH} не найдена${NC}"
        exit 1
    }
    
    echo "📋 Текущая ветка и коммит:"
    git branch --show-current || echo "⚠️  Не удалось определить ветку"
    git log --oneline -1 || echo "⚠️  Не удалось получить коммит"
    
    echo ""
    echo "🔄 Обновление кода из GitHub..."
    git remote set-url origin https://github.com/makhotin07/trade_bot.git || true
    
    # Пытаемся сделать pull
    if git pull origin master 2>&1; then
        echo -e "${GREEN}✅ Код успешно обновлен${NC}"
    else
        echo -e "${YELLOW}⚠️  Git pull не удался, пробуем обновить вручную...${NC}"
        git fetch origin master || true
        git reset --hard origin/master || true
    fi
    
    echo ""
    echo "📦 Обновление зависимостей..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo "✅ Активировано виртуальное окружение .venv"
    elif [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Активировано виртуальное окружение venv"
    else
        echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено${NC}"
    fi
    
    pip install -r requirements.txt --upgrade --quiet || {
        echo -e "${RED}❌ Ошибка установки зависимостей${NC}"
        exit 1
    }
    
    echo ""
    echo "🔄 Перезапуск бота..."
    if systemctl is-active --quiet bytbit-bot.service 2>/dev/null; then
        systemctl restart bytbit-bot.service
        echo -e "${GREEN}✅ Бот перезапущен через systemd${NC}"
        sleep 2
        systemctl status bytbit-bot.service --no-pager || true
    elif [ -f "scripts/restart.sh" ]; then
        bash scripts/restart.sh
        echo -e "${GREEN}✅ Бот перезапущен через скрипт${NC}"
    else
        echo -e "${YELLOW}⚠️  Бот не запущен. Запустите вручную: python main.py${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Деплой завершен успешно${NC}"
    echo ""
    echo "📋 Финальный статус:"
    git log --oneline -1 || true
EOF

echo ""
echo -e "${GREEN}✅ Ручной деплой завершен${NC}"

