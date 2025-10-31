"""
Telegram бот для управления
"""
import logging
import os
import telebot
from .utils import save_user_config, get_user_config, is_user_enabled, load_json, TOKENS_FILE
from .config import TOKEN
from datetime import datetime, timezone
import pytz

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)

def get_scheduler():
    """Получает экземпляр планировщика"""
    try:
        from .scheduler import scheduler
        return scheduler
    except ImportError:
        return None


@bot.message_handler(commands=['start'])
def start_message(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_config = get_user_config(user_id)
    
    if not user_config:
        user_config = {
            "enabled": False,
            "api_key": "",
            "api_secret": "",
            "leverage": 10,
            "margin": 20
        }
        save_user_config(user_id, user_config)
    
    text = (
        "🤖 Бот для автоматической торговли на Bybit\n\n"
        "Команды:\n"
        "/start - Начать работу\n"
        "/status - Статус бота\n"
        "/balance - Текущий баланс\n"
        "/list - Список запланированных токенов\n"
        "/enable - Включить бота\n"
        "/disable - Выключить бота\n"
        "/set_api - Настроить API ключи\n"
        "/set_leverage - Настроить плечо\n"
        "/set_margin - Настроить маржу\n"
        "/help - Помощь"
    )
    
    bot.reply_to(message, text)


@bot.message_handler(commands=['help'])
def help_message(message):
    """Обработчик команды /help"""
    text = (
        "📖 Помощь по использованию бота\n\n"
        "1. Настройте API ключи Bybit командой /set_api\n"
        "2. Настройте плечо командой /set_leverage\n"
        "3. Настройте маржу командой /set_margin\n"
        "4. Включите бота командой /enable\n\n"
        "Бот будет автоматически открывать позиции при появлении новых токенов в канале @TokenSplashBybit"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=['status'])
def status_message(message):
    """Показывает статус бота"""
    user_id = message.from_user.id
    user_config = get_user_config(user_id)
    
    enabled = "✅ Включен" if user_config.get("enabled", False) else "❌ Выключен"
    api_key_set = "✅ Настроен" if user_config.get("api_key") else "❌ Не настроен"
    leverage = user_config.get("leverage", 10)
    margin = user_config.get("margin", 20)
    
    text = (
        f"📊 Статус бота:\n\n"
        f"Состояние: {enabled}\n"
        f"API ключ: {api_key_set}\n"
        f"Плечо: {leverage}x\n"
        f"Маржа: {margin} USDT"
    )
    
    bot.reply_to(message, text)


@bot.message_handler(commands=['enable'])
def enable_bot(message):
    """Включает бота"""
    user_id = message.from_user.id
    user_config = get_user_config(user_id)
    
    if not user_config.get("api_key") or not user_config.get("api_secret"):
        bot.reply_to(message, "❌ Сначала настройте API ключи командой /set_api")
        return
    
    user_config["enabled"] = True
    save_user_config(user_id, user_config)
    bot.reply_to(message, "✅ Бот включен")


@bot.message_handler(commands=['disable'])
def disable_bot(message):
    """Выключает бота"""
    user_id = message.from_user.id
    user_config = get_user_config(user_id)
    
    user_config["enabled"] = False
    save_user_config(user_id, user_config)
    bot.reply_to(message, "❌ Бот выключен")


@bot.message_handler(commands=['set_api'])
def set_api(message):
    """Настройка API ключей"""
    bot.reply_to(message, (
        "🔑 Настройка API ключей Bybit\n\n"
        "Отправьте API ключ и секрет в формате:\n"
        "<API_KEY> <API_SECRET>\n\n"
        "Например:\n"
        "abc123xyz secret456"
    ))
    bot.register_next_step_handler(message, process_api_keys)


def process_api_keys(message):
    """Обрабатывает введённые API ключи"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    parts = text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Неверный формат. Используйте: <API_KEY> <API_SECRET>")
        return
    
    api_key = parts[0]
    api_secret = parts[1]
    
    user_config = get_user_config(user_id)
    user_config["api_key"] = api_key
    user_config["api_secret"] = api_secret
    save_user_config(user_id, user_config)
    
    bot.reply_to(message, "✅ API ключи сохранены")


@bot.message_handler(commands=['set_leverage'])
def set_leverage(message):
    """Настройка плеча"""
    bot.reply_to(message, "⚙️ Введите значение плеча (например, 10):")
    bot.register_next_step_handler(message, process_leverage)


def process_leverage(message):
    """Обрабатывает введённое плечо"""
    user_id = message.from_user.id
    
    try:
        leverage = float(message.text.strip())
        if leverage < 1 or leverage > 100:
            bot.reply_to(message, "❌ Плечо должно быть от 1 до 100")
            return
        
        user_config = get_user_config(user_id)
        user_config["leverage"] = leverage
        save_user_config(user_id, user_config)
        
        bot.reply_to(message, f"✅ Плечо установлено: {leverage}x")
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат числа")


@bot.message_handler(commands=['list'])
def list_tokens(message):
    """Показывает список запланированных токенов"""
    try:
        tokens = load_json(TOKENS_FILE)
        
        if not tokens:
            bot.reply_to(message, "📋 Нет запланированных токенов")
            return
        
        scheduled_jobs = []
        scheduler = get_scheduler()
        if scheduler:
            scheduled_jobs = {job.id for job in scheduler.get_jobs()}
        
        text = "📋 Запланированные токены:\n\n"
        
        sorted_tokens = sorted(
            tokens.items(),
            key=lambda x: x[1].get("result_datetime", ""),
            reverse=False
        )
        
        tz_moscow = pytz.timezone("Europe/Moscow")
        now = datetime.now(tz_moscow)
        future_count = 0
        
        for token_key, token_data in sorted_tokens:
            token = token_data.get("token", "N/A")
            result_datetime_str = token_data.get("result_datetime")
            
            is_scheduled = False
            if result_datetime_str:
                try:
                    result_date = datetime.fromisoformat(result_datetime_str)
                    if result_date.tzinfo is None:
                        result_date = tz_moscow.localize(result_date)
                    else:
                        result_date = result_date.astimezone(tz_moscow)
                    
                    job_id = f"token_{token}_{result_date.isoformat()}"
                    is_scheduled = job_id in scheduled_jobs
                    
                    if result_date > now:
                        future_count += 1
                        status = "✅" if is_scheduled else "⚠️"
                        date_formatted = result_date.strftime("%d.%m.%Y %H:%M")
                        text += f"{status} {token} - {date_formatted} MSK\n"
                except Exception as e:
                    logger.error(f"Error processing token {token}: {e}")
        
        if future_count == 0:
            text = "📋 Нет активных запланированных токенов (все даты прошли)"
        
        text += f"\nВсего активных: {future_count}"
        
        bot.reply_to(message, text)
        
    except Exception as e:
        logger.error(f"Error listing tokens: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Ошибка получения списка: {str(e)}")


@bot.message_handler(commands=['balance'])
def balance_message(message):
    """Показывает текущий баланс на Bybit"""
    user_id = message.from_user.id
    from .trading import get_balance
    get_balance(user_id, bot)


@bot.message_handler(commands=['set_margin'])
def set_margin(message):
    """Настройка маржи"""
    bot.reply_to(message, "💰 Введите размер маржи в USDT (например, 20):")
    bot.register_next_step_handler(message, process_margin)


def process_margin(message):
    """Обрабатывает введённую маржу"""
    user_id = message.from_user.id
    
    try:
        margin = float(message.text.strip())
        if margin < 1:
            bot.reply_to(message, "❌ Маржа должна быть больше 0")
            return
        
        user_config = get_user_config(user_id)
        user_config["margin"] = margin
        save_user_config(user_id, user_config)
        
        bot.reply_to(message, f"✅ Маржа установлена: {margin} USDT")
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат числа")


def start_telebot():
    """Запускает Telegram бота"""
    logger.info("[Telebot] Starting...")
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        logger.error(f"[Telebot] Error: {e}", exc_info=True)
        start_telebot()

