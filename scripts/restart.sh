#!/bin/bash
# Скрипт для перезапуска бота на сервере

cd "$(dirname "$0")"

# Активируем виртуальное окружение если есть
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Останавливаем старый процесс (если запущен через python)
pkill -f "python.*main.py" || true
pkill -f "bytbit-bot" || true

# Небольшая задержка
sleep 2

# Запускаем бота в фоне
nohup python main.py > bot.log 2>&1 &

echo "Bot restarted successfully"
echo "PID: $!"

