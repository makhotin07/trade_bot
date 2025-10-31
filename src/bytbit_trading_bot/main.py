"""
Главный модуль для запуска бота
"""
import logging
import threading
import asyncio
from .parser import start_telethon
from .bot import start_telebot
from .scheduler import start_scheduler

logger = logging.getLogger(__name__)


def run_telebot():
    """Запускает Telebot в отдельном потоке"""
    try:
        start_telebot()
    except Exception as e:
        logger.error(f"[Main] Ошибка запуска Telebot: {e}", exc_info=True)


def main():
    """Главная функция запуска бота"""
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("[Main] Запуск бота...")
    
    # Запускаем планировщик
    start_scheduler()
    
    # Запускаем Telebot в отдельном потоке
    telebot_thread = threading.Thread(target=run_telebot, daemon=True)
    telebot_thread.start()
    logger.info("[Main] Telebot запущен в отдельном потоке")
    
    # Запускаем Telethon в основном потоке (async)
    try:
        asyncio.run(start_telethon())
    except KeyboardInterrupt:
        logger.info("[Main] Получен сигнал остановки")
    except Exception as e:
        logger.error(f"[Main] Ошибка запуска Telethon: {e}", exc_info=True)
        raise

