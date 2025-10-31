# Бот для автоматической торговли на Bybit

Telegram-бот для автоматизации торговли на бирже Bybit на основе сигналов из канала @TokenSplashBybit.

## Описание

Бот автоматически:
- Парсит сообщения из Telegram-канала @TokenSplashBybit
- Извлекает информацию о предстоящих token splash событиях
- Планирует открытие длинных позиций на момент result
- Открывает позиции с тейк-профитами (TP1: +3%, TP2: +6%) и стоп-лоссом (SL: -2%)

## Установка

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd protiv_treiderov
```

2. Создайте виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Для разработки (с линтерами и тестами):
```bash
pip install -r requirements-dev.txt
```

## Конфигурация

1. Получите необходимые API ключи:
   - **Telegram Bot Token**: От [@BotFather](https://t.me/BotFather)
   - **Telegram API ID и API Hash**: От [my.telegram.org](https://my.telegram.org)
   - **Bybit API Key и Secret**: От [Bybit API](https://www.bybit.com/app/user/api-management)

2. Настройте переменные окружения или отредактируйте `src/bytbit_trading_bot/config.py`:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`

## Использование

1. Запустите бота:
```bash
python main.py
```

2. В Telegram найдите вашего бота и отправьте команду `/start`

3. Настройте бота через команды:
   - `/set_api` - Настроить API ключи Bybit
   - `/set_leverage` - Настроить плечо (по умолчанию 10x)
   - `/set_margin` - Настроить маржу в USDT (по умолчанию 20 USDT)
   - `/enable` - Включить бота
   - `/disable` - Выключить бота
   - `/status` - Проверить статус
   - `/list` - Список запланированных токенов

## Структура проекта

```
.
├── src/
│   └── bytbit_trading_bot/
│       ├── __init__.py
│       ├── main.py          # Главный модуль запуска
│       ├── config.py        # Конфигурация и константы
│       ├── bot.py           # Telegram бот для управления
│       ├── parser.py        # Парсер Telegram канала
│       ├── trading.py       # Модуль торговли на Bybit
│       ├── scheduler.py     # Планировщик задач
│       ├── utils.py         # Вспомогательные функции
│       └── data/            # Папка с данными (JSON файлы)
│           ├── users.json   # Данные пользователей
│           └── tokens.json  # Данные о токенах
├── tests/                   # Тесты
│   ├── __init__.py
│   ├── test_utils.py
│   └── test_config.py
├── scripts/                 # Скрипты для деплоя
│   ├── restart.sh
│   └── bytbit-bot.service
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # CI/CD pipeline
├── main.py                  # Точка входа
├── setup.py                 # Установка пакета
├── requirements.txt         # Зависимости
├── requirements-dev.txt     # Dev зависимости
├── pyproject.toml          # Конфигурация линтеров
├── .flake8                 # Конфигурация flake8
└── README.md               # Документация
```

## Разработка

### Линтинг и форматирование

```bash
# Проверка форматирования
black --check src/ tests/

# Форматирование кода
black src/ tests/

# Проверка сортировки импортов
isort --check-only src/ tests/

# Сортировка импортов
isort src/ tests/

# Линтинг
flake8 src/ tests/

# Проверка типов
mypy src/
```

### Тестирование

```bash
# Запуск тестов
pytest tests/ -v

# С покрытием
pytest tests/ -v --cov=src/bytbit_trading_bot
```

## CI/CD

Проект использует GitHub Actions для CI/CD:

1. **Lint** - проверка кода линтерами (flake8, black, isort, mypy)
2. **Test** - запуск тестов
3. **Deploy** - автоматический деплой на сервер при пуше в main/master

### Настройка деплоя

1. Добавьте секреты в GitHub:
   - `SSH_PRIVATE_KEY` - приватный SSH ключ для доступа к серверу
   - `SERVER_HOST` - IP или домен сервера
   - `SERVER_USER` - пользователь для SSH
   - `SERVER_PATH` - путь к проекту на сервере

2. Настройте сервер:
   ```bash
   # Клонируйте репозиторий
   git clone <your-repo-url> /path/to/project
   cd /path/to/project
   
   # Создайте виртуальное окружение
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   
   # Настройте systemd service (опционально)
   sudo cp scripts/bytbit-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable bytbit-bot.service
   sudo systemctl start bytbit-bot.service
   ```

## Деплой на сервер

### Автоматический деплой

При пуше в ветку `main` или `master` автоматически запускается деплой через GitHub Actions.

### Ручной деплой

```bash
# На сервере
cd /path/to/project
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt --upgrade
bash scripts/restart.sh
# или
sudo systemctl restart bytbit-bot.service
```

## Важные замечания

⚠️ **ВНИМАНИЕ**: Торговля криптовалютами связана с высокими рисками. Используйте этот бот на свой страх и риск. Автор не несёт ответственности за возможные финансовые потери.

- Тестируйте сначала на демо-счёте
- Не используйте суммы, которые не готовы потерять
- Прошлые результаты не гарантируют будущих
- Убедитесь, что понимаете риски торговли с плечом

## Параметры торговли

По умолчанию используются следующие параметры:
- **TP1**: +3% (40% позиции)
- **TP2**: +6% (30% позиции)
- **SL**: -2% (30% позиции)
- **Buy**: 70% от расчётного объёма

Эти параметры можно изменить в файле `src/bytbit_trading_bot/config.py`.

## Лицензия

Проект создан в образовательных целях. Используйте на свой риск.
