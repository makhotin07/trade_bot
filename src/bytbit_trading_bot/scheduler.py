"""
Планировщик задач
"""
import logging
from datetime import datetime
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


def schedule_token(token, result_date):
    """
    Планирует открытие позиции для токена
    
    Args:
        token: Символ токена (например, LA)
        result_date: datetime объект с датой result
    """
    global scheduler
    
    if scheduler is None:
        logger.error("[Scheduler] Планировщик не инициализирован")
        return
    
    logger.info(f"[Scheduler] Планирование токена {token} на {result_date}")
    
    scheduler.add_job(
        notify_all_enabled_users,
        trigger=DateTrigger(run_date=result_date),
        args=[token],
        id=f"token_{token}_{result_date.isoformat()}",
        replace_existing=True
    )


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

