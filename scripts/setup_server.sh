#!/bin/bash
# Скрипт для первоначальной настройки сервера (запустить один раз)

set -e

echo "🚀 Начальная настройка сервера для Bybit Trading Bot..."

# Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get upgrade -y

# Установка необходимых пакетов
echo "📦 Установка зависимостей..."
apt-get install -y python3 python3-pip python3-venv git

# Создание директории проекта
PROJECT_DIR="/root/trade_bot"
echo "📁 Создание директории проекта: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Клонирование репозитория
if [ ! -d ".git" ]; then
    echo "📥 Клонирование репозитория..."
    git clone https://github.com/makhotin07/trade_bot.git .
else
    echo "📥 Репозиторий уже существует, обновление..."
    git pull origin master
fi

# Создание виртуального окружения
echo "🐍 Создание виртуального окружения..."
python3 -m venv .venv
source .venv/bin/activate

# Установка зависимостей
echo "📦 Установка зависимостей Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание директорий для данных
echo "📁 Создание директорий для данных..."
mkdir -p src/bytbit_trading_bot/data
echo "{}" > src/bytbit_trading_bot/data/users.json
echo "{}" > src/bytbit_trading_bot/data/tokens.json

# Настройка systemd service
echo "⚙️  Настройка systemd service..."
cp scripts/bytbit-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bytbit-bot.service

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Настройте config.py: nano src/bytbit_trading_bot/config.py"
echo "2. Запустите бота: systemctl start bytbit-bot.service"
echo "3. Проверьте статус: systemctl status bytbit-bot.service"

