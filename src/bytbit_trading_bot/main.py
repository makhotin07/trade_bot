"""
Главный файл для запуска бота
"""
import logging
import threading
import time
import asyncio
from .bot import start_telebot
from .parser import start_telethon
from .scheduler import start_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)


def main():
    """Главная функция запуска бота"""
    logger.info("[Main] Starting bot...")
    
    try:
        # Запускаем планировщик
        threading.Thread(target=start_scheduler, daemon=True).start()
        time.sleep(1)  # Даём время на инициализацию
        
        # Запускаем telebot
        threading.Thread(target=start_telebot, daemon=True).start()
        time.sleep(1)
        
        # Telethon в отдельном потоке
        def run_telethon():
            logger.info("[Telethon Thread] Starting...")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(start_telethon())
            except Exception as e:
                logger.error(f"[Telethon Thread] Failed: {e}", exc_info=True)
                # Пытаемся перезапустить через некоторое время
                time.sleep(5)
                run_telethon()
        
        threading.Thread(target=run_telethon, daemon=True).start()
        
        # Keep main thread alive
        logger.info("[Main] Bot started successfully")
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"[Main] Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

