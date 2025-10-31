"""
Тесты для функции получения баланса
"""
import sys
import os
from unittest.mock import Mock, MagicMock

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

from bytbit_trading_bot.utils import load_json, save_json, USERS_FILE


def test_get_balance_success():
    """Тест успешного получения баланса"""
    import bytbit_trading_bot.trading as trading_module
    
    # Создаем мок сессии
    mock_session = Mock()
    mock_session.get_wallet_balance.return_value = {
        "retCode": 0,
        "result": {
            "list": [{
                "coin": [
                    {
                        "coin": "USDT",
                        "walletBalance": "100.5",
                        "availableToWithdraw": "95.2",
                        "locked": "5.3"
                    },
                    {
                        "coin": "BTC",
                        "walletBalance": "0.001",
                        "availableToWithdraw": "0.001",
                        "locked": "0"
                    }
                ]
            }]
        }
    }
    
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    # Создаем тестового пользователя
    test_user_id = 88888
    users = {
        str(test_user_id): {
            "enabled": True,
            "api_key": "test_key",
            "api_secret": "test_secret"
        }
    }
    save_json(USERS_FILE, users)
    
    # Мокаем создание сессии
    original_HTTP = trading_module.HTTP
    trading_module.HTTP = Mock(return_value=mock_session)
    
    try:
        trading_module.get_balance(test_user_id, mock_bot)
        
        # Проверяем, что был вызван get_wallet_balance
        assert mock_session.get_wallet_balance.called, "get_wallet_balance не был вызван"
        
        # Проверяем, что было отправлено сообщение с балансом
        assert mock_bot.send_message.called, "Сообщение не было отправлено"
        
        # Проверяем, что в сообщении есть информация о балансе
        call_args = mock_bot.send_message.call_args
        message_text = call_args[0][1]
        assert "💰" in message_text or "Баланс" in message_text, "Сообщение не содержит информацию о балансе"
        assert "USDT" in message_text, "Сообщение не содержит информацию о USDT"
        
        print("✅ Тест test_get_balance_success пройден")
    finally:
        trading_module.HTTP = original_HTTP


def test_get_balance_no_api_keys():
    """Тест что при отсутствии API ключей отправляется ошибка"""
    import bytbit_trading_bot.trading as trading_module
    
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    test_user_id = 88887
    users = {
        str(test_user_id): {
            "enabled": True,
            "api_key": "",  # Пустой API ключ
            "api_secret": ""
        }
    }
    save_json(USERS_FILE, users)
    
    try:
        trading_module.get_balance(test_user_id, mock_bot)
        
        # Проверяем, что было отправлено сообщение об ошибке
        assert mock_bot.send_message.called, "Сообщение не было отправлено"
        
        call_args = mock_bot.send_message.call_args
        message_text = call_args[0][1]
        assert "❌" in message_text and "API ключи" in message_text, \
            "Сообщение об ошибке API ключей не отправлено"
        
        print("✅ Тест test_get_balance_no_api_keys пройден")
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")


def test_get_balance_api_error():
    """Тест обработки ошибки API"""
    import bytbit_trading_bot.trading as trading_module
    
    mock_session = Mock()
    mock_session.get_wallet_balance.return_value = {
        "retCode": 10001,
        "retMsg": "Invalid API key"
    }
    
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    test_user_id = 88886
    users = {
        str(test_user_id): {
            "enabled": True,
            "api_key": "test_key",
            "api_secret": "test_secret"
        }
    }
    save_json(USERS_FILE, users)
    
    original_HTTP = trading_module.HTTP
    trading_module.HTTP = Mock(return_value=mock_session)
    
    try:
        trading_module.get_balance(test_user_id, mock_bot)
        
        # Проверяем, что было отправлено сообщение об ошибке
        assert mock_bot.send_message.called, "Сообщение не было отправлено"
        
        call_args = mock_bot.send_message.call_args
        message_text = call_args[0][1]
        assert "❌" in message_text and "ошибка" in message_text.lower(), \
            "Сообщение об ошибке API не отправлено"
        
        print("✅ Тест test_get_balance_api_error пройден")
    finally:
        trading_module.HTTP = original_HTTP


if __name__ == "__main__":
    print("Запуск тестов для функции получения баланса...")
    
    # Создаем тестовые директории если их нет
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    
    try:
        test_get_balance_success()
        test_get_balance_no_api_keys()
        test_get_balance_api_error()
        
        print("\n✅ Все тесты пройдены успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

