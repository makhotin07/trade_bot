"""
Планировщик задач
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from .utils import load_json, is_user_enabled, TOKENS_FILE, USERS_FILE
from .trading import long_token
from .bot import bot

logger = logging.getLogger(__name__)

scheduler = None


def notify_all_enabled_users(token):
    """
    Уведомляет всех включенных пользователей и открывает позиции
    
    Args:
        token: Символ токена (например, LA)
    """
    logger.info(f"[Scheduler] Запуск открытия позиций для токена {token}")
    
    users = load_json(USERS_FILE)
    
    for user_id_str, user_config in users.items():
        user_id = int(user_id_str)
        
        if is_user_enabled(user_id):
            try:
                logger.info(f"[Scheduler] Открытие позиции для пользователя {user_id}")
                long_token(token, user_id, bot)
            except Exception as e:
                logger.error(f"[Scheduler] Ошибка открытия позиции для {user_id}: {e}", exc_info=True)


def notify_reminder(token, result_date):
    """
    Отправляет напоминание всем включенным пользователям за день до события
    
    Args:
        token: Символ токена (например, LA)
        result_date: datetime объект с датой result
    """
    logger.info(f"[Scheduler] Отправка напоминания о токене {token} за день до события")
    
    users = load_json(USERS_FILE)
    
    # Форматируем дату для сообщения
    from datetime import timezone
    import pytz
    tz_moscow = pytz.timezone("Europe/Moscow")
    if result_date.tzinfo is None:
        result_date_display = tz_moscow.localize(result_date)
    else:
        result_date_display = result_date.astimezone(tz_moscow)
    
    date_str = result_date_display.strftime("%d.%m.%Y %H:%M MSK")
    
    message_text = (
        f"🔔 Напоминание\n\n"
        f"Завтра ({date_str}) запланирован токен:\n"
        f"**{token}**\n\n"
        f"Бот автоматически откроет позицию в указанное время."
    )
    
    for user_id_str, user_config in users.items():
        user_id = int(user_id_str)
        
        if is_user_enabled(user_id):
            try:
                logger.info(f"[Scheduler] Отправка напоминания пользователю {user_id} о токене {token}")
                bot.send_message(user_id, message_text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"[Scheduler] Ошибка отправки напоминания пользователю {user_id}: {e}", exc_info=True)


def schedule_token(token, result_date):
    """
    Планирует открытие позиции для токена и напоминание за день до события
    
    Args:
        token: Символ токена (например, LA)
        result_date: datetime объект с датой result
    """
    global scheduler
    
    if scheduler is None:
        logger.error("[Scheduler] Планировщик не инициализирован")
        return
    
    logger.info(f"[Scheduler] Планирование токена {token} на {result_date}")
    
    # Планируем открытие позиции
    scheduler.add_job(
        notify_all_enabled_users,
        trigger=DateTrigger(run_date=result_date),
        args=[token],
        id=f"token_{token}_{result_date.isoformat()}",
        replace_existing=True
    )
    
    # Планируем напоминание за день до события
    reminder_date = result_date - timedelta(days=1)
    
    # Проверяем, что напоминание в будущем (не в прошлом)
    from datetime import timezone
    now = datetime.now(result_date.tzinfo if result_date.tzinfo else timezone.utc)
    if reminder_date > now:
        scheduler.add_job(
            notify_reminder,
            trigger=DateTrigger(run_date=reminder_date),
            args=[token, result_date],
            id=f"reminder_{token}_{result_date.isoformat()}",
            replace_existing=True
        )
        logger.info(f"[Scheduler] Напоминание для токена {token} запланировано на {reminder_date}")
    else:
        logger.info(f"[Scheduler] Напоминание для токена {token} пропущено (дата в прошлом)")


def start_scheduler():
    """Запускает планировщик"""
    global scheduler
    
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.start()
        logger.info("[Scheduler] Планировщик запущен")
    
    # Загружаем сохранённые токены и планируем их
    tokens = load_json(TOKENS_FILE)
    
    for token_key, token_data in tokens.items():
        try:
            result_datetime_str = token_data.get("result_datetime")
            if result_datetime_str:
                from datetime import datetime
                result_date = datetime.fromisoformat(result_datetime_str)
                
                # Проверяем, что дата в будущем
                from datetime import timezone
                now = datetime.now(result_date.tzinfo if result_date.tzinfo else timezone.utc)
                if result_date > now:
                    token = token_data.get("token")
                    schedule_token(token, result_date)
        except Exception as e:
            logger.error(f"[Scheduler] Ошибка планирования токена {token_key}: {e}", exc_info=True)

