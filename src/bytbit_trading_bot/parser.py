"""
Парсер Telegram канала
"""
import re
import logging
import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient, events
from .utils import parse_result_date, load_json, save_json, TOKENS_FILE
from .config import API_ID, API_HASH, SESSION_NAME, CHANNEL, POST_REGEX, MESSAGES_HISTORY_LIMIT
from .scheduler import schedule_token

logger = logging.getLogger(__name__)

client = None


async def process_message(message_text):
    """
    Обрабатывает сообщение из канала и находит новые анонсы.
    
    Логика:
    - Парсит сообщение по регулярному выражению
    - Извлекает токен и дату Result
    - Если время Result в будущем — ставит задачу в календарь
    
    Args:
        message_text: Текст сообщения
        
    Returns:
        True если токен был обработан и запланирован, False если нет
    """
    if not message_text:
        return False
    
    # Парсим сообщение по регулярке (ищем формат: ТОКЕН\n...Result DD.MM.YYYY HH:MM UTC или без UTC)
    match = re.match(POST_REGEX, message_text, re.DOTALL | re.MULTILINE)
    
    if not match:
        logger.debug(f"[Telethon] Сообщение не соответствует паттерну: {message_text[:100]}")
        return False
    
    # Извлекаем токен и дату Result
    token = match.group("token")
    result_date_str = match.group("result_date")
    
    logger.info(f"[Telethon] Найден анонс: токен={token}, Result={result_date_str}")
    
    # Парсим дату из строки в datetime объект
    result_date = parse_result_date(result_date_str)
    
    if not result_date:
        logger.error(f"[Telethon] Не удалось распарсить дату: {result_date_str}")
        return False
    
    # Проверяем, что дата Result в будущем
    now = datetime.now(result_date.tzinfo if result_date.tzinfo else timezone.utc)
    if result_date <= now:
        logger.info(f"[Telethon] Дата {result_date_str} уже прошла, пропускаем")
        return False
    
    # Проверяем, не добавлен ли уже этот токен (чтобы не дублировать)
    tokens = load_json(TOKENS_FILE)
    token_key = f"{token}_{result_date_str}"
    
    if token_key in tokens:
        logger.info(f"[Telethon] Токен {token} уже добавлен, пропускаем")
        return False
    
    # Сохраняем токен в файл
    tokens[token_key] = {
        "token": token,
        "result_date": result_date_str,
        "result_datetime": result_date.isoformat(),
        "added_at": datetime.now().isoformat()
    }
    save_json(TOKENS_FILE, tokens)
    
    # Ставим задачу в календарь (планировщик)
    schedule_token(token, result_date)
    
    logger.info(f"[Telethon] ✅ Токен {token} запланирован на {result_date}")
    return True


async def check_recent_messages():
    """
    Читает последние 50 сообщений из @TokenSplashBybit при запуске.
    
    Находит новые анонсы и ставит задачи в календарь для будущих событий.
    """
    try:
        logger.info(f"[Telethon] 📖 Читаю последние {MESSAGES_HISTORY_LIMIT} сообщений из {CHANNEL}...")
        
        messages_processed = 0
        tokens_found = 0
        
        # Читаем последние сообщения из канала
        async for message in client.iter_messages(CHANNEL, limit=MESSAGES_HISTORY_LIMIT):
            if message.text:
                # Обрабатываем каждое сообщение (находит анонсы и планирует задачи)
                if await process_message(message.text):
                    tokens_found += 1
                messages_processed += 1
        
        logger.info(f"[Telethon] ✅ Проверено {messages_processed} сообщений, найдено {tokens_found} новых токенов с будущими датами")
        
    except Exception as e:
        error_msg = str(e)
        if "bot" in error_msg.lower() or "BotMethodInvalidError" in error_msg:
            logger.error(f"[Telethon] ⚠️  Не удалось прочитать историю сообщений: авторизация как бот")
            logger.error(f"[Telethon] ⚠️  Решение: удалите файл my_session.session и перезапустите бота")
            logger.error(f"[Telethon] ⚠️  При запросе 'Please enter your phone (or bot token):' введите НОМЕР ТЕЛЕФОНА, а не токен бота!")
            logger.info(f"[Telethon] ⚠️  Бот продолжит работать, но будет обрабатывать только новые сообщения")
        else:
            logger.error(f"[Telethon] Ошибка проверки последних сообщений: {e}", exc_info=True)


async def start_telethon():
    """
    Запускает клиент Telethon и обрабатывает сообщения из канала.
    
    Логика работы:
    1. Подключается к Telegram через ваш аккаунт (нужен API ID и Hash)
    2. Читает последние 50 сообщений из @TokenSplashBybit
    3. Находит новые анонсы
    4. Если время Result в будущем — ставит задачу в календарь
    5. Слушает новые сообщения в реальном времени
    """
    global client
    
    if not API_ID or not API_HASH:
        logger.error("[Telethon] API_ID или API_HASH не настроены")
        return
    
    # Создаём клиент Telethon с вашими API credentials
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    # Обработчик новых сообщений (для работы в реальном времени)
    @client.on(events.NewMessage(chats=CHANNEL))
    async def handler(event):
        """Обработчик новых сообщений из канала"""
        try:
            await process_message(event.message.text)
        except Exception as e:
            logger.error(f"[Telethon] Ошибка обработки сообщения: {e}", exc_info=True)
    
    try:
        # Шаг 1: Подключаемся к Telegram через ваш аккаунт (НЕ через бота!)
        # Важно: client.start() должен запросить номер телефона, а не токен бота
        # Если вы видите запрос "Please enter your phone (or bot token):" - введите номер телефона
        await client.start()
        
        # Проверяем, что авторизация прошла как пользователь, а не как бот
        me = await client.get_me()
        if me.bot:
            logger.error("[Telethon] ОШИБКА: Авторизация прошла как бот! Нужна авторизация через номер телефона пользователя.")
            logger.error("[Telethon] Удалите файл my_session.session и перезапустите бота")
            return
        
        logger.info(f"[Telethon] Успешно подключен к Telegram как пользователь: {me.first_name} (@{me.username})")
        
        # Шаг 2: Читаем последние 50 сообщений из канала
        # Шаг 3: Находим новые анонсы
        # Шаг 4: Если время Result в будущем — ставим задачу в календарь
        await check_recent_messages()
        
        # Шаг 5: Продолжаем слушать новые сообщения в реальном времени
        logger.info("[Telethon] Начинаю слушать новые сообщения из канала...")
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"[Telethon] Ошибка запуска: {e}", exc_info=True)
        raise

