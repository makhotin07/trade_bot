#!/bin/bash
# Скрипт для первоначальной настройки сервера

set -e

echo "🚀 Начало развертывания Bybit Trading Bot..."

# Переменные (настройте под себя)
PROJECT_DIR="/root/trade_bot"
REPO_URL="https://github.com/makhotin07/trade_bot.git"
PYTHON_VERSION="3.11"

# Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get upgrade -y

# Установка необходимых пакетов
echo "📦 Установка зависимостей..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    htop \
    curl \
    wget \
    nano \
    ufw

# Создание директории проекта
echo "📁 Создание директории проекта..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Клонирование репозитория
if [ ! -d ".git" ]; then
    echo "📥 Клонирование репозитория..."
    git clone "$REPO_URL" .
else
    echo "📥 Обновление репозитория..."
    git pull origin master
fi

# Создание виртуального окружения
if [ ! -d ".venv" ]; then
    echo "🐍 Создание виртуального окружения..."
    python3 -m venv .venv
fi

# Активация виртуального окружения и установка зависимостей
echo "📦 Установка зависимостей Python..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Создание директории для данных
echo "📁 Создание директорий для данных..."
mkdir -p src/bytbit_trading_bot/data

# Создание файлов конфигурации если их нет
if [ ! -f "src/bytbit_trading_bot/data/users.json" ]; then
    echo "{}" > src/bytbit_trading_bot/data/users.json
fi

if [ ! -f "src/bytbit_trading_bot/data/tokens.json" ]; then
    echo "{}" > src/bytbit_trading_bot/data/tokens.json
fi

# Настройка прав доступа
chmod +x scripts/restart.sh

echo "✅ Развертывание завершено!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Настройте переменные окружения или отредактируйте config.py"
echo "2. Запустите бота: python main.py"
echo "3. Или используйте systemd service: sudo cp scripts/bytbit-bot.service /etc/systemd/system/"

