"""
Вспомогательные функции
"""
import json
import os
import logging
from datetime import datetime
import pytz
from decimal import Decimal

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")


def load_json(file_path):
    """Загружает JSON файл"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}", exc_info=True)
            return {}
    return {}


def save_json(file_path, data):
    """Сохраняет данные в JSON файл"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}", exc_info=True)


def parse_result_date(date_str):
    """
    Парсит дату из формата DD.MM.YYYY HH:MM или DD.MM.YYYY HH:MM UTC
    Если указано UTC, конвертирует в московское время (UTC+3)
    """
    try:
        is_utc = 'UTC' in date_str.upper()
        date_str = date_str.strip().replace(' UTC', '').replace('UTC', '').strip()
        dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        
        tz_moscow = pytz.timezone("Europe/Moscow")
        if is_utc:
            dt = pytz.timezone("UTC").localize(dt).astimezone(tz_moscow)
        else:
            dt = tz_moscow.localize(dt)
        
        return dt
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {e}")
        return None


def round_to_tick_size(value, tick_size):
    """Округляет значение до шага цены"""
    if tick_size == 0:
        return value
    return float(Decimal(str(value)) // Decimal(str(tick_size)) * Decimal(str(tick_size)))


def round_to_qty_step(qty, qty_step):
    """Округляет количество до шага объёма"""
    if qty_step == 0:
        return qty
    return float(Decimal(str(qty)) // Decimal(str(qty_step)) * Decimal(str(qty_step)))


def get_user_config(user_id):
    """Получает конфигурацию пользователя"""
    users = load_json(USERS_FILE)
    return users.get(str(user_id), {})


def save_user_config(user_id, config):
    """Сохраняет конфигурацию пользователя"""
    users = load_json(USERS_FILE)
    users[str(user_id)] = config
    save_json(USERS_FILE, users)


def is_user_enabled(user_id):
    """Проверяет, включен ли бот для пользователя"""
    user_config = get_user_config(user_id)
    return user_config.get("enabled", False)

