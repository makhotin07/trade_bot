"""
Конфигурация бота
"""
import os

# Telegram Bot Token (от @BotFather)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8343388162:AAEpXZwry5GsVWADfhBXpJdszYoK9PaJnxs")

# Telegram API credentials (от my.telegram.org)
# Получите на https://my.telegram.org/apps
# API_ID должен быть числом, например: 12345678
# API_HASH должен быть строкой из 32 символов, например: "abcdef1234567890abcdef1234567890"

API_ID = 16223511

API_HASH = '66c83b36a77573871b55b72c6c57018f'

# Сессия Telethon
SESSION_NAME = "my_session"

# Канал для парсинга
CHANNEL = '@TokenSplashBybit'

# Регулярка для парсинга токена и Result даты
# Поддерживает формат: ТОКЕН\n...Result DD.MM.YYYY HH:MM (UTC) или DD.MM.YYYY HH:MM
POST_REGEX = r'^(?P<token>\w+)\n.*?Result (?P<result_date>\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})(?:\s+UTC)?'

# Количество последних сообщений для проверки при запуске
MESSAGES_HISTORY_LIMIT = 50

# Параметры торговли
TP1_PCT = 3.0  # Тейк-профит 1 (%)
TP2_PCT = 6.0  # Тейк-профит 2 (%)
STOP_LOSS_PCT = 2.0  # Стоп-лосс (%)
BUY_PCT = 70.0  # Процент от объёма для покупки

# Часовой пояс
TIMEZONE = "Europe/Moscow"
