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
    logger.debug(f"[Telethon] Обработка сообщения (первые 200 символов): {message_text[:200]}")
    
    # Сначала пробуем re.match (с начала строки)
    match = re.match(POST_REGEX, message_text, re.DOTALL | re.MULTILINE)
    
    # Если не совпало, пробуем re.search (в любом месте сообщения)
    if not match:
        match = re.search(POST_REGEX, message_text, re.DOTALL | re.MULTILINE)
        if match:
            logger.info(f"[Telethon] Паттерн найден через re.search (не с начала строки)")
    
    if not match:
        # Логируем только первые 5 несовпавших сообщений, чтобы не засорять логи
        logger.debug(f"[Telethon] Сообщение не соответствует паттерну: {message_text[:100]}")
        # Проверяем, есть ли хотя бы слово "Result" в сообщении
        if "Result" in message_text or "result" in message_text.lower():
            logger.warning(f"[Telethon] ⚠️  В сообщении есть 'Result', но оно не совпало с паттерном!")
            logger.warning(f"[Telethon] ⚠️  Паттерн: {POST_REGEX}")
            logger.warning(f"[Telethon] ⚠️  Сообщение: {message_text[:500]}")
            # Пытаемся найти токен вручную
            lines = message_text.split('\n')
            if len(lines) > 0:
                logger.warning(f"[Telethon] ⚠️  Первая строка сообщения: {lines[0]}")
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
    
    logger.info(f"[Telethon] Сохранение токена в файл {TOKENS_FILE}")
    save_json(TOKENS_FILE, tokens)
    
    # Проверяем, что токен действительно сохранился
    tokens_after = load_json(TOKENS_FILE)
    if token_key in tokens_after:
        logger.info(f"[Telethon] ✅ Токен {token_key} успешно сохранен в файл")
    else:
        logger.error(f"[Telethon] ❌ Ошибка: токен {token_key} не найден в файле после сохранения!")
    
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
        logger.info(f"[Telethon] Используется регулярное выражение: {POST_REGEX}")
        logger.info(f"[Telethon] Файл для сохранения токенов: {TOKENS_FILE}")
        
        messages_processed = 0
        tokens_found = 0
        messages_with_text = 0
        messages_matched = 0
        
        # Читаем последние сообщения из канала
        async for message in client.iter_messages(CHANNEL, limit=MESSAGES_HISTORY_LIMIT):
            messages_processed += 1
            
            if message.text:
                messages_with_text += 1
                # Логируем первые несколько сообщений для отладки
                if messages_with_text <= 3:
                    logger.info(f"[Telethon] Пример сообщения #{messages_with_text}: {message.text[:200]}...")
                
                # Обрабатываем каждое сообщение (находит анонсы и планирует задачи)
                result = await process_message(message.text)
                if result:
                    tokens_found += 1
                    messages_matched += 1
                    logger.info(f"[Telethon] ✅ Токен успешно обработан (всего найдено: {tokens_found})")
        
        logger.info(f"[Telethon] ✅ Статистика:")
        logger.info(f"[Telethon]    - Всего сообщений проверено: {messages_processed}")
        logger.info(f"[Telethon]    - Сообщений с текстом: {messages_with_text}")
        logger.info(f"[Telethon]    - Сообщений с совпадением паттерна: {messages_matched}")
        logger.info(f"[Telethon]    - Найдено новых токенов с будущими датами: {tokens_found}")
        
        # Проверяем, что файл токенов существует и содержит данные
        tokens = load_json(TOKENS_FILE)
        logger.info(f"[Telethon] ✅ Всего токенов в файле: {len(tokens)}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Telethon] ❌ Ошибка проверки последних сообщений: {e}", exc_info=True)
        if "bot" in error_msg.lower() or "BotMethodInvalidError" in error_msg:
            logger.error(f"[Telethon] ⚠️  Не удалось прочитать историю сообщений: авторизация как бот")
            logger.error(f"[Telethon] ⚠️  Решение: удалите файл my_session.session и перезапустите бота")
            logger.error(f"[Telethon] ⚠️  При запросе 'Please enter your phone (or bot token):' введите НОМЕР ТЕЛЕФОНА, а не токен бота!")
            logger.info(f"[Telethon] ⚠️  Бот продолжит работать, но будет обрабатывать только новые сообщения")
        else:
            logger.error(f"[Telethon] Полная трассировка ошибки:", exc_info=True)


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
    import os
    global client
    
    if not API_ID or not API_HASH:
        logger.error("[Telethon] API_ID или API_HASH не настроены")
        return
    
    # Определяем путь к файлу сессии
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    session_path = os.path.join(project_root, f"{SESSION_NAME}.session")
    
    # Если файл сессии не найден в корне проекта, используем относительный путь
    if not os.path.exists(session_path):
        session_path = SESSION_NAME
    
    # Создаём клиент Telethon с вашими API credentials
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    # Обработчик новых сообщений (для работы в реальном времени)
    @client.on(events.NewMessage(chats=CHANNEL))
    async def handler(event):
        """Обработчик новых сообщений из канала"""
        try:
            await process_message(event.message.text)
        except Exception as e:
            logger.error(f"[Telethon] Ошибка обработки сообщения: {e}", exc_info=True)
    
    try:
        # Проверяем существование файла сессии (используем абсолютный путь)
        # Определяем рабочую директорию проекта
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))  # поднимаемся на 2 уровня вверх от parser.py
        session_file = os.path.join(project_root, f"{SESSION_NAME}.session")
        session_exists = os.path.exists(session_file)
        
        # Если не нашли в корне проекта, пробуем в текущей директории
        if not session_exists:
            session_file = f"{SESSION_NAME}.session"
            session_exists = os.path.exists(session_file)
        
        # Шаг 1: Подключаемся к Telegram через ваш аккаунт (НЕ через бота!)
        # Сначала пытаемся подключиться без интерактивного ввода
        try:
            await client.connect()
        except Exception as e:
            logger.error(f"[Telethon] Ошибка подключения: {e}")
            if not session_exists:
                logger.error(f"[Telethon] ❌ Файл сессии {session_file} не найден!")
                logger.error(f"[Telethon] ❌ Запустите: python3 scripts/init_telethon_session.py")
                return
            raise
        
        # Проверяем, авторизован ли пользователь
        is_authorized = await client.is_user_authorized()
        logger.info(f"[Telethon] Проверка авторизации: is_authorized={is_authorized}, session_file={session_file}, session_exists={session_exists}")
        
        if not is_authorized:
            logger.warning(f"[Telethon] ⚠️  Сессия существует, но не авторизована!")
            logger.warning(f"[Telethon] ⚠️  Файл сессии: {session_file}")
            logger.warning(f"[Telethon] ⚠️  Файл существует: {os.path.exists(session_file)}")
            logger.warning(f"[Telethon] ⚠️  Возможно, сессия была удалена или повреждена при обновлении.")
            logger.warning(f"[Telethon] ⚠️  Необходимо пересоздать сессию.")
            logger.warning(f"[Telethon] ⚠️  Выполните на сервере:")
            logger.warning(f"[Telethon] ⚠️  1. cd /root/trade_bot")
            logger.warning(f"[Telethon] ⚠️  2. source .venv/bin/activate")
            logger.warning(f"[Telethon] ⚠️  3. python3 scripts/init_telethon_session.py")
            logger.warning(f"[Telethon] ⚠️  4. Введите номер телефона и код подтверждения из Telegram")
            logger.warning(f"[Telethon] ⚠️  5. После успешной авторизации перезапустите бота:")
            logger.warning(f"[Telethon] ⚠️     systemctl restart bytbit-bot.service")
            
            if not session_exists:
                logger.error(f"[Telethon] ❌ Файл сессии {session_file} не найден!")
                logger.error(f"[Telethon] ❌ Запустите: python3 scripts/init_telethon_session.py")
                return
            
            logger.error(f"[Telethon] ❌ Бот не может запуститься без авторизованной сессии. Создайте сессию вручную.")
            
            # Сессия существует, но не авторизована - пробуем через переменные окружения
            phone = os.getenv("TELEGRAM_PHONE")
            password = os.getenv("TELEGRAM_PASSWORD")
            
            if phone:
                logger.info(f"[Telethon] Попытка авторизации через номер телефона из переменных окружения")
                try:
                    await client.send_code_request(phone)
                    code = os.getenv("TELEGRAM_CODE")
                    if code:
                        await client.sign_in(phone, code, password=password)
                    else:
                        logger.error(f"[Telethon] Требуется TELEGRAM_CODE для авторизации")
                        return
                except Exception as e:
                    logger.error(f"[Telethon] Ошибка авторизации через переменные окружения: {e}")
                    logger.error(f"[Telethon] Создайте сессию вручную (см. инструкцию выше)")
                    return
            else:
                logger.error(f"[Telethon] ❌ Сессия не авторизована и нет TELEGRAM_PHONE в переменных окружения")
                logger.error(f"[Telethon] ❌ Создайте сессию вручную или установите TELEGRAM_PHONE и TELEGRAM_CODE")
                return
        
        # Проверяем, что авторизация прошла как пользователь, а не как бот
        me = await client.get_me()
        if me.bot:
            logger.error("[Telethon] ОШИБКА: Авторизация прошла как бот! Нужна авторизация через номер телефона пользователя.")
            logger.error("[Telethon] Удалите файл my_session.session и перезапустите бота")
            return
        
        logger.info(f"[Telethon] Успешно подключен к Telegram как пользователь: {me.first_name} (@{me.username})")
        
        # Проверяем доступ к каналу
        try:
            entity = await client.get_entity(CHANNEL)
            logger.info(f"[Telethon] ✅ Канал доступен: {entity.title} (ID: {entity.id})")
        except Exception as e:
            logger.error(f"[Telethon] ❌ Ошибка доступа к каналу {CHANNEL}: {e}")
            return
        
        # Шаг 2: Читаем последние 50 сообщений из канала
        # Шаг 3: Находим новые анонсы
        # Шаг 4: Если время Result в будущем — ставим задачу в календарь
        await check_recent_messages()
        
        # Шаг 5: Продолжаем слушать новые сообщения в реальном времени
        logger.info("[Telethon] Начинаю слушать новые сообщения из канала...")
        await client.run_until_disconnected()
    except EOFError:
        logger.error("[Telethon] ❌ Ошибка: требуется интерактивный ввод для авторизации")
        logger.error("[Telethon] ❌ Создайте сессию вручную один раз (см. инструкцию выше)")
        logger.error("[Telethon] ❌ Или используйте переменные окружения TELEGRAM_PHONE и TELEGRAM_CODE")
    except Exception as e:
        logger.error(f"[Telethon] Ошибка запуска: {e}", exc_info=True)
        raise

