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

#### Способ 1: Использование скрипта деплоя

```bash
# На вашем локальном компьютере
./scripts/deploy_manual.sh

# Или с указанием параметров сервера
SERVER_USER=root SERVER_HOST=91.229.8.171 SERVER_PATH=/root/trade_bot ./scripts/deploy_manual.sh
```

#### Способ 2: Ручное обновление на сервере

```bash
# 1. Подключитесь к серверу
ssh root@your-server-ip

# 2. Перейдите в директорию проекта
cd /root/trade_bot

# 3. Обновите код из GitHub
git pull origin master

# 4. Обновите зависимости
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. Перезапустите бота
systemctl restart bytbit-bot.service

# 6. Проверьте статус
systemctl status bytbit-bot.service
journalctl -u bytbit-bot.service -f
```

#### Проверка статуса деплоя

Если автоматический деплой не сработал:

1. **Проверьте GitHub Actions:**
   - Откройте https://github.com/makhotin07/trade_bot/actions
   - Посмотрите последний workflow run
   - Если есть ошибки, проверьте логи

2. **Проверьте секреты GitHub:**
   - Settings → Secrets and variables → Actions
   - Убедитесь, что есть: `SSH_PRIVATE_KEY`, `SERVER_HOST`, `SERVER_USER`, `SERVER_PATH`

3. **Проверьте SSH подключение:**
   ```bash
   ssh -i ~/.ssh/id_rsa root@91.229.8.171
   ```

4. **Проверьте статус бота на сервере:**
   ```bash
   ssh root@91.229.8.171 "cd /root/trade_bot && git log --oneline -1"
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
