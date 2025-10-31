#!/bin/bash
# Скрипт для перезапуска бота на сервере

# Переходим в директорию проекта
cd /root/trade_bot || exit 1

# Перезапускаем через systemd если настроен
if systemctl is-active --quiet bytbit-bot.service 2>/dev/null; then
    systemctl restart bytbit-bot.service
    echo "Bot restarted via systemd"
    exit 0
fi

# Если systemd не настроен, перезапускаем вручную
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Останавливаем старый процесс
pkill -f "python.*main.py" || true
sleep 2

# Запускаем бота в фоне
nohup python main.py > bot.log 2>&1 &

echo "Bot restarted successfully"
echo "PID: $!"

