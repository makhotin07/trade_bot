# Bybit Trading Bot

Telegram-бот для автоматической торговли на бирже Bybit на основе сигналов из канала @TokenSplashBybit.

## Описание

Бот автоматически:
- Парсит сообщения из Telegram-канала @TokenSplashBybit через Telethon
- Извлекает информацию о предстоящих token splash событиях (токен и дату Result)
- Планирует открытие длинных позиций на момент Result
- Открывает позиции с тейк-профитами (TP1: +3%, TP2: +6%) и стоп-лоссом (SL: -2%)

## Быстрый старт

### 1. Установка зависимостей

```bash
git clone <your-repo-url>
cd protiv_treiderov
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Отредактируйте `src/bytbit_trading_bot/config.py`:
- `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
- `API_ID` и `API_HASH` - от my.telegram.org

### 3. Создание Telethon сессии

Запустите один раз для авторизации:
```bash
python3 scripts/init_telethon_session.py
```
Введите номер телефона и код подтверждения из Telegram.

### 4. Запуск

```bash
python main.py
```

## Развертывание на сервере

### Автоматическое развертывание

1. Настройте GitHub Secrets:
   - `SSH_PRIVATE_KEY` - приватный SSH ключ
   - `SERVER_HOST` - IP сервера
   - `SERVER_USER` - пользователь (обычно root)
   - `SERVER_PATH` - путь к проекту (например `/root/trade_bot`)

2. При пуше в `main`/`master` автоматически запустится деплой.

### Ручное развертывание

```bash
# 1. Подключитесь к серверу
ssh root@your-server-ip

# 2. Установите зависимости системы
apt-get update
apt-get install -y python3 python3-pip python3-venv git

# 3. Клонируйте проект
cd /root
git clone https://github.com/your-username/trade_bot.git
cd trade_bot

# 4. Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Создайте директории для данных
mkdir -p src/bytbit_trading_bot/data
echo "{}" > src/bytbit_trading_bot/data/users.json
echo "{}" > src/bytbit_trading_bot/data/tokens.json

# 6. Создайте Telethon сессию
python3 scripts/init_telethon_session.py

# 7. Настройте systemd service
cp scripts/bytbit-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bytbit-bot.service
systemctl start bytbit-bot.service

# 8. Проверьте статус
systemctl status bytbit-bot.service
journalctl -u bytbit-bot.service -f
```

## Команды бота

- `/start` - Начать настройку
- `/set_api` - Настроить API ключи Bybit
- `/set_leverage` - Настроить плечо (по умолчанию 10x)
- `/set_margin` - Настроить маржу в USDT
- `/enable` - Включить бота
- `/disable` - Выключить бота
- `/status` - Проверить статус
- `/list` - Список запланированных токенов

## Структура проекта

```
.
├── src/bytbit_trading_bot/   # Основной код
│   ├── bot.py               # Telegram бот
│   ├── parser.py            # Парсер канала
│   ├── trading.py           # Торговля на Bybit
│   ├── scheduler.py         # Планировщик
│   └── config.py            # Конфигурация
├── scripts/                  # Скрипты
│   ├── init_telethon_session.py  # Инициализация сессии
│   └── bytbit-bot.service   # Systemd service
├── main.py                  # Точка входа
└── requirements.txt         # Зависимости
```

## Параметры торговли

По умолчанию:
- **TP1**: +3% (40% позиции)
- **TP2**: +6% (30% позиции)
- **SL**: -2% (30% позиции)
- **Buy**: 70% от объёма

Изменить можно в `src/bytbit_trading_bot/config.py`.

## ⚠️ Внимание

Торговля криптовалютами связана с высокими рисками. Используйте на свой страх и риск.

## Лицензия

Проект создан в образовательных целях.
