"""
Парсер Telegram канала
"""
import re
import logging
import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient, events
from .utils import parse_result_date, load_json, save_json, TOKENS_FILE, is_user_enabled, USERS_FILE
from .config import API_ID, API_HASH, SESSION_NAME, CHANNEL, POST_REGEX, MESSAGES_HISTORY_LIMIT, TOKEN
from .scheduler import schedule_token
import pytz

logger = logging.getLogger(__name__)

client = None


def notify_users_about_new_token(token, result_date_str, result_date):
    """
    Отправляет уведомление всем включенным пользователям о новом токене
    
    Args:
        token: Символ токена
        result_date_str: Строка с датой Result
        result_date: datetime объект с датой Result
    """
    try:
        from .bot import bot
        
        users = load_json(USERS_FILE)
        
        # Форматируем дату для сообщения
        tz_moscow = pytz.timezone("Europe/Moscow")
        if result_date.tzinfo is None:
            result_date_display = tz_moscow.localize(result_date)
        else:
            result_date_display = result_date.astimezone(tz_moscow)
        
        date_str = result_date_display.strftime("%d.%m.%Y %H:%M MSK")
        
        message_text = (
            f"🆕 Новый токен добавлен!\n\n"
            f"📌 Токен: **{token}**\n"
            f"📅 Дата Result: {date_str}\n\n"
            f"✅ Токен запланирован для автоматической покупки"
        )
        
        for user_id_str, user_config in users.items():
            user_id = int(user_id_str)
            if is_user_enabled(user_id):
                try:
                    bot.send_message(user_id, message_text, parse_mode='Markdown')
                    logger.info(f"[Parser] Уведомление отправлено пользователю {user_id} о токене {token}")
                except Exception as e:
                    logger.error(f"[Parser] Ошибка отправки уведомления пользователю {user_id}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"[Parser] Ошибка отправки уведомлений о новом токене: {e}", exc_info=True)


async def process_message(message_text):
    """
    Обрабатывает сообщение из канала и находит новые анонсы.
    
    Args:
        message_text: Текст сообщения
        
    Returns:
        True если токен был обработан и запланирован, False если нет
    """
    if not message_text:
        logger.debug("[Telethon] process_message: сообщение пустое")
        return False
    
    logger.debug(f"[Telethon] process_message: начинаю обработку сообщения длиной {len(message_text)} символов")
    
    match = re.match(POST_REGEX, message_text, re.DOTALL | re.MULTILINE)
    if not match:
        match = re.search(POST_REGEX, message_text, re.DOTALL | re.MULTILINE)
    
    if not match:
        if "Result" in message_text or "result" in message_text.lower():
            logger.warning(f"[Telethon] Сообщение содержит 'Result', но не соответствует паттерну: {message_text[:200]}")
            logger.debug(f"[Telethon] Используемый паттерн: {POST_REGEX}")
        return False
    
    # Извлекаем токен и дату Result
    token = match.group("token")
    result_date_str = match.group("result_date")
    
    logger.info(f"[Telethon] Найден токен: {token}, дата Result: {result_date_str}")
    
    result_date = parse_result_date(result_date_str)
    if not result_date:
        logger.error(f"[Telethon] Не удалось распарсить дату: {result_date_str}")
        return False
    
    now = datetime.now(result_date.tzinfo if result_date.tzinfo else timezone.utc)
    if result_date <= now:
        logger.debug(f"[Telethon] Дата {result_date_str} уже прошла, пропускаем")
        return False
    
    tokens = load_json(TOKENS_FILE)
    token_key = f"{token}_{result_date_str}"
    
    if token_key in tokens:
        logger.debug(f"[Telethon] Токен {token} уже добавлен, пропускаем")
        return False
    
    tokens[token_key] = {
        "token": token,
        "result_date": result_date_str,
        "result_datetime": result_date.isoformat(),
        "added_at": datetime.now().isoformat()
    }
    save_json(TOKENS_FILE, tokens)
    schedule_token(token, result_date)
    
    logger.info(f"[Telethon] Токен {token} запланирован на {result_date}")
    
    # Отправляем уведомление всем включенным пользователям
    notify_users_about_new_token(token, result_date_str, result_date)
    
    return True


async def check_recent_messages():
    """
    Читает последние 50 сообщений из @TokenSplashBybit при запуске.
    
    Находит новые анонсы и ставит задачи в календарь для будущих событий.
    """
    try:
        logger.info(f"[Telethon] Читаю последние {MESSAGES_HISTORY_LIMIT} сообщений из {CHANNEL}")
        
        messages_processed = 0
        tokens_found = 0
        
        async for message in client.iter_messages(CHANNEL, limit=MESSAGES_HISTORY_LIMIT):
            messages_processed += 1
            if message.text and await process_message(message.text):
                tokens_found += 1
        
        tokens = load_json(TOKENS_FILE)
        logger.info(f"[Telethon] Проверено {messages_processed} сообщений, найдено {tokens_found} новых токенов, всего в файле: {len(tokens)}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Telethon] Ошибка проверки последних сообщений: {e}", exc_info=True)
        if "bot" in error_msg.lower() or "BotMethodInvalidError" in error_msg:
            logger.error(f"[Telethon] Не удалось прочитать историю сообщений: авторизация как бот")
            logger.error(f"[Telethon] Решение: удалите файл my_session.session и перезапустите бота")
            logger.error(f"[Telethon] При запросе введите НОМЕР ТЕЛЕФОНА, а не токен бота!")
        else:
            logger.error(f"[Telethon] Полная трассировка ошибки:", exc_info=True)


async def start_telethon():
    """Запускает клиент Telethon и обрабатывает сообщения из канала"""
    import os
    global client
    
    if not API_ID or not API_HASH:
        logger.error("[Telethon] API_ID или API_HASH не настроены")
        return
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    session_path = os.path.join(project_root, f"{SESSION_NAME}.session")
    
    if not os.path.exists(session_path):
        session_path = SESSION_NAME
    
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    @client.on(events.NewMessage(chats=CHANNEL))
    async def handler(event):
        """Обработчик новых сообщений из канала"""
        try:
            logger.info(f"[Telethon] Получено новое сообщение из канала {CHANNEL}")
            if event.message.text:
                logger.debug(f"[Telethon] Текст сообщения: {event.message.text[:200]}")
                processed = await process_message(event.message.text)
                if processed:
                    logger.info(f"[Telethon] Сообщение успешно обработано и токен запланирован")
                else:
                    logger.debug(f"[Telethon] Сообщение не содержит подходящий анонс токена")
            else:
                logger.debug(f"[Telethon] Сообщение не содержит текста (возможно, медиа-сообщение)")
        except Exception as e:
            logger.error(f"[Telethon] Ошибка обработки сообщения: {e}", exc_info=True)
    
    try:
        session_file = os.path.join(project_root, f"{SESSION_NAME}.session")
        session_exists = os.path.exists(session_file)
        
        if not session_exists:
            session_file = f"{SESSION_NAME}.session"
            session_exists = os.path.exists(session_file)
        
        try:
            await client.connect()
        except Exception as e:
            logger.error(f"[Telethon] Ошибка подключения: {e}")
            if not session_exists:
                logger.error(f"[Telethon] Файл сессии не найден. Запустите: python3 scripts/init_telethon_session.py")
                return
            raise
        
        is_authorized = await client.is_user_authorized()
        
        if not is_authorized:
            logger.error(f"[Telethon] Сессия не авторизована. Выполните: python3 scripts/init_telethon_session.py")
            logger.error(f"[Telethon] При запросе введите НОМЕР ТЕЛЕФОНА, а НЕ токен бота!")
            return
        
        me = await client.get_me()
        if me.bot:
            logger.error("[Telethon] ОШИБКА: Авторизация прошла как бот! Удалите my_session.session и пересоздайте через номер телефона")
            return
        
        logger.info(f"[Telethon] Подключен как пользователь: {me.first_name} (@{me.username})")
        
        try:
            entity = await client.get_entity(CHANNEL)
            logger.info(f"[Telethon] Канал доступен: {entity.title}")
        except Exception as e:
            logger.error(f"[Telethon] Ошибка доступа к каналу {CHANNEL}: {e}")
            return
        
        await check_recent_messages()
        
        logger.info("[Telethon] Ожидание новых сообщений из канала...")
        await client.run_until_disconnected()
    except EOFError:
        logger.error("[Telethon] Ошибка: требуется интерактивный ввод для авторизации")
        logger.error("[Telethon] Создайте сессию вручную: python3 scripts/init_telethon_session.py")
    except Exception as e:
        logger.error(f"[Telethon] Ошибка запуска: {e}", exc_info=True)
        raise

