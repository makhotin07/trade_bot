"""
Тесты для функции напоминания о токенах
"""
import sys
import os
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch, MagicMock

# Мокаем зависимости до импорта
mock_scheduler_module = MagicMock()
mock_scheduler_module.BackgroundScheduler = Mock
mock_scheduler_module.DateTrigger = Mock
sys.modules['apscheduler'] = MagicMock()
sys.modules['apscheduler.schedulers'] = MagicMock()
sys.modules['apscheduler.schedulers.background'] = mock_scheduler_module
sys.modules['apscheduler.triggers'] = MagicMock()
sys.modules['apscheduler.triggers.date'] = mock_scheduler_module

# Мокаем pybit
sys.modules['pybit'] = MagicMock()
sys.modules['pybit.unified_trading'] = MagicMock()

# Мокаем telebot
mock_telebot = MagicMock()
sys.modules['telebot'] = mock_telebot

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bytbit_trading_bot.utils import load_json, save_json, TOKENS_FILE, USERS_FILE


def test_notify_reminder():
    """Тест отправки напоминания"""
    # Импортируем модуль до патчинга
    import bytbit_trading_bot.scheduler as scheduler_module
    
    # Создаем мок бота
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    # Создаем тестового пользователя
    test_user_id = 12345
    users = {
        str(test_user_id): {
            "enabled": True,
            "api_key": "test_key",
            "api_secret": "test_secret"
        }
    }
    
    # Сохраняем пользователя
    save_json(USERS_FILE, users)
    
    # Создаем дату result (завтра)
    tz_moscow = pytz.timezone("Europe/Moscow")
    result_date = datetime.now(tz_moscow) + timedelta(days=1)
    
    # Мокаем bot в модуле
    original_bot = scheduler_module.bot
    scheduler_module.bot = mock_bot
    
    try:
        scheduler_module.notify_reminder("TEST", result_date)
    finally:
        scheduler_module.bot = original_bot
    
    # Проверяем, что сообщение было отправлено
    assert mock_bot.send_message.called, "Сообщение не было отправлено"
    
    # Проверяем аргументы
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == test_user_id, "Неправильный user_id"
    assert "TEST" in call_args[0][1], "Токен не найден в сообщении"
    assert "Напоминание" in call_args[0][1], "Текст напоминания не найден"
    
    print("✅ Тест notify_reminder пройден")


def test_notify_reminder_disabled_user():
    """Тест что напоминание не отправляется отключенным пользователям"""
    import bytbit_trading_bot.scheduler as scheduler_module
    
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    # Создаем отключенного пользователя
    test_user_id = 12346
    users = {
        str(test_user_id): {
            "enabled": False,
            "api_key": "test_key",
            "api_secret": "test_secret"
        }
    }
    
    save_json(USERS_FILE, users)
    
    tz_moscow = pytz.timezone("Europe/Moscow")
    result_date = datetime.now(tz_moscow) + timedelta(days=1)
    
    original_bot = scheduler_module.bot
    scheduler_module.bot = mock_bot
    
    try:
        scheduler_module.notify_reminder("TEST", result_date)
    finally:
        scheduler_module.bot = original_bot
    
    # Проверяем, что сообщение НЕ было отправлено
    assert not mock_bot.send_message.called, "Сообщение отправлено отключенному пользователю"
    
    print("✅ Тест notify_reminder_disabled_user пройден")


def test_schedule_token_with_reminder():
    """Тест планирования токена с напоминанием"""
    import bytbit_trading_bot.scheduler as scheduler_module
    
    # Создаем мок планировщика
    mock_scheduler = Mock()
    mock_scheduler.add_job = Mock()
    
    tz_moscow = pytz.timezone("Europe/Moscow")
    result_date = datetime.now(tz_moscow) + timedelta(days=2)  # Через 2 дня
    
    original_scheduler = scheduler_module.scheduler
    scheduler_module.scheduler = mock_scheduler
    
    try:
        scheduler_module.schedule_token("TEST", result_date)
    finally:
        scheduler_module.scheduler = original_scheduler
    
    # Проверяем, что были добавлены 2 задачи: открытие позиции и напоминание
    assert mock_scheduler.add_job.call_count == 2, f"Ожидалось 2 задачи, получено {mock_scheduler.add_job.call_count}"
    
    # Проверяем что задачи были добавлены
    call_ids = [call[1]['id'] for call in mock_scheduler.add_job.call_args_list]
    assert any('token_TEST' in call_id for call_id in call_ids), "Задача открытия позиции не найдена"
    assert any('reminder_TEST' in call_id for call_id in call_ids), "Задача напоминания не найдена"
    
    print("✅ Тест schedule_token_with_reminder пройден")


def test_schedule_token_past_reminder():
    """Тест что напоминание не планируется если оно в прошлом"""
    import bytbit_trading_bot.scheduler as scheduler_module
    
    mock_scheduler = Mock()
    mock_scheduler.add_job = Mock()
    
    tz_moscow = pytz.timezone("Europe/Moscow")
    # Дата result завтра, но напоминание (за день до) уже в прошлом
    result_date = datetime.now(tz_moscow) + timedelta(hours=12)
    
    original_scheduler = scheduler_module.scheduler
    scheduler_module.scheduler = mock_scheduler
    
    try:
        scheduler_module.schedule_token("TEST", result_date)
    finally:
        scheduler_module.scheduler = original_scheduler
    
    # Должна быть только одна задача (открытие позиции), напоминание пропущено
    assert mock_scheduler.add_job.call_count >= 1, "Должна быть хотя бы одна задача"
    
    # Проверяем что нет задачи напоминания
    call_ids = [call[1]['id'] for call in mock_scheduler.add_job.call_args_list]
    reminder_found = any('reminder_TEST' in call_id for call_id in call_ids)
    assert not reminder_found, "Напоминание не должно планироваться если оно в прошлом"
    
    print("✅ Тест schedule_token_past_reminder пройден")


if __name__ == "__main__":
    print("Запуск тестов для функции напоминания...")
    
    # Создаем тестовые директории если их нет
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(TOKENS_FILE), exist_ok=True)
    
    try:
        test_notify_reminder()
        test_notify_reminder_disabled_user()
        test_schedule_token_with_reminder()
        test_schedule_token_past_reminder()
        
        print("\n✅ Все тесты пройдены успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

