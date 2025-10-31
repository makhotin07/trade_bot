"""
Тесты для улучшенной функции торговли
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch

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


def test_order_retry_on_failure():
    """Тест повторных попыток при неудачном размещении ордера"""
    import bytbit_trading_bot.trading as trading_module
    
    # Создаем мок сессии
    mock_session = Mock()
    
    # Первые две попытки неудачны, третья успешна
    mock_session.set_leverage.return_value = {"retCode": 0}
    mock_session.get_instruments_info.return_value = {
        "retCode": 0,
        "result": {
            "list": [{
                "tickSize": "0.01",
                "lotSizeFilter": {"qtyStep": "1", "minQty": "1"}
            }]
        }
    }
    mock_session.get_tickers.return_value = {
        "retCode": 0,
        "result": {"list": [{"lastPrice": "1.0"}]}
    }
    mock_session.get_wallet_balance.return_value = {
        "retCode": 0,
        "result": {"list": [{"coin": [{"walletBalance": "100"}]}]}
    }
    mock_session.get_open_positions.return_value = {
        "retCode": 0,
        "result": {"list": [{"symbol": "TESTUSDT", "size": "100"}]}
    }
    
    # Первые две попытки неудачны, третья успешна, затем TP ордера успешны
    buy_order_calls = 0
    
    def place_order_side_effect(*args, **kwargs):
        nonlocal buy_order_calls
        # Проверяем, это ордер покупки (Market Buy) или TP (Limit Sell)
        if kwargs.get("order_type") == "Market" and kwargs.get("side") == "Buy":
            buy_order_calls += 1
            if buy_order_calls == 1:
                return {"retCode": 10001, "retMsg": "Insufficient balance"}
            elif buy_order_calls == 2:
                return {"retCode": 10001, "retMsg": "Insufficient balance"}
            else:
                return {"retCode": 0, "result": {"orderId": "12345"}}
        else:
            # TP ордера всегда успешны
            return {"retCode": 0, "result": {"orderId": f"tp_{buy_order_calls}"}}
    
    mock_session.place_order.side_effect = place_order_side_effect
    
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    # Создаем тестового пользователя
    test_user_id = 99999
    users = {
        str(test_user_id): {
            "enabled": True,
            "api_key": "test_key",
            "api_secret": "test_secret",
            "leverage": 10,
            "margin": 20
        }
    }
    save_json(USERS_FILE, users)
    
    # Мокаем создание сессии
    original_HTTP = trading_module.HTTP
    trading_module.HTTP = Mock(return_value=mock_session)
    
    try:
        trading_module.long_token("TEST", test_user_id, mock_bot)
        
        # Проверяем, что было 3 попытки покупки (плюс TP ордера)
        buy_calls = [call for call in mock_session.place_order.call_args_list 
                    if call[1].get("order_type") == "Market" and call[1].get("side") == "Buy"]
        assert len(buy_calls) == 3, f"Ожидалось 3 попытки покупки, получено {len(buy_calls)}"
        
        # Проверяем, что в итоге отправилось успешное сообщение
        success_calls = [call for call in mock_bot.send_message.call_args_list 
                        if call[0][1].startswith("✅")]
        assert len(success_calls) > 0, "Сообщение об успехе не отправлено"
        
        print("✅ Тест test_order_retry_on_failure пройден")
    finally:
        trading_module.HTTP = original_HTTP


def test_order_check_result():
    """Тест проверки результата размещения ордера"""
    import bytbit_trading_bot.trading as trading_module
    
    mock_session = Mock()
    mock_session.set_leverage.return_value = {"retCode": 0}
    mock_session.get_instruments_info.return_value = {
        "retCode": 0,
        "result": {"list": [{"tickSize": "0.01", "lotSizeFilter": {"qtyStep": "1", "minQty": "1"}}]}
    }
    mock_session.get_tickers.return_value = {
        "retCode": 0,
        "result": {"list": [{"lastPrice": "1.0"}]}
    }
    mock_session.get_wallet_balance.return_value = {
        "retCode": 0,
        "result": {"list": [{"coin": [{"walletBalance": "100"}]}]}
    }
    mock_session.get_open_positions.return_value = {
        "retCode": 0,
        "result": {"list": [{"symbol": "TESTUSDT", "size": "100"}]}
    }
    
    # Ордер успешен
    mock_session.place_order.return_value = {
        "retCode": 0,
        "result": {"orderId": "12345"}
    }
    
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    test_user_id = 99998
    users = {
        str(test_user_id): {
            "enabled": True,
            "api_key": "test_key",
            "api_secret": "test_secret",
            "leverage": 10,
            "margin": 20
        }
    }
    save_json(USERS_FILE, users)
    
    original_HTTP = trading_module.HTTP
    trading_module.HTTP = Mock(return_value=mock_session)
    
    try:
        trading_module.long_token("TEST", test_user_id, mock_bot)
        
        # Проверяем, что place_order был вызван
        assert mock_session.place_order.called, "place_order не был вызван"
        
        # Проверяем, что было отправлено успешное сообщение
        success_calls = [call for call in mock_bot.send_message.call_args_list 
                        if "✅" in call[0][1] and "Лонг" in call[0][1]]
        assert len(success_calls) > 0, "Сообщение об успехе не отправлено"
        
        print("✅ Тест test_order_check_result пройден")
    finally:
        trading_module.HTTP = original_HTTP


def test_order_failure_after_all_retries():
    """Тест что при всех неудачных попытках отправляется ошибка"""
    import bytbit_trading_bot.trading as trading_module
    
    mock_session = Mock()
    mock_session.set_leverage.return_value = {"retCode": 0}
    mock_session.get_instruments_info.return_value = {
        "retCode": 0,
        "result": {"list": [{"tickSize": "0.01", "lotSizeFilter": {"qtyStep": "1", "minQty": "1"}}]}
    }
    mock_session.get_tickers.return_value = {
        "retCode": 0,
        "result": {"list": [{"lastPrice": "1.0"}]}
    }
    mock_session.get_wallet_balance.return_value = {
        "retCode": 0,
        "result": {"list": [{"coin": [{"walletBalance": "100"}]}]}
    }
    
    # Все попытки неудачны
    mock_session.place_order.return_value = {
        "retCode": 10001,
        "retMsg": "Insufficient balance"
    }
    
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    test_user_id = 99997
    users = {
        str(test_user_id): {
            "enabled": True,
            "api_key": "test_key",
            "api_secret": "test_secret",
            "leverage": 10,
            "margin": 20
        }
    }
    save_json(USERS_FILE, users)
    
    original_HTTP = trading_module.HTTP
    trading_module.HTTP = Mock(return_value=mock_session)
    
    try:
        trading_module.long_token("TEST", test_user_id, mock_bot)
        
        # Проверяем, что было MAX_RETRIES попыток
        assert mock_session.place_order.call_count == trading_module.MAX_RETRIES, \
            f"Ожидалось {trading_module.MAX_RETRIES} попыток"
        
        # Проверяем, что было отправлено сообщение об ошибке
        error_calls = [call for call in mock_bot.send_message.call_args_list 
                      if "❌" in call[0][1] and "попыток" in call[0][1]]
        assert len(error_calls) > 0, "Сообщение об ошибке не отправлено"
        
        print("✅ Тест test_order_failure_after_all_retries пройден")
    finally:
        trading_module.HTTP = original_HTTP


def test_position_verification():
    """Тест проверки открытой позиции после размещения ордера"""
    import bytbit_trading_bot.trading as trading_module
    
    mock_session = Mock()
    mock_session.set_leverage.return_value = {"retCode": 0}
    mock_session.get_instruments_info.return_value = {
        "retCode": 0,
        "result": {"list": [{"tickSize": "0.01", "lotSizeFilter": {"qtyStep": "1", "minQty": "1"}}]}
    }
    mock_session.get_tickers.return_value = {
        "retCode": 0,
        "result": {"list": [{"lastPrice": "1.0"}]}
    }
    mock_session.get_wallet_balance.return_value = {
        "retCode": 0,
        "result": {"list": [{"coin": [{"walletBalance": "100"}]}]}
    }
    mock_session.place_order.return_value = {
        "retCode": 0,
        "result": {"orderId": "12345"}
    }
    
    # Позиция не найдена
    mock_session.get_open_positions.return_value = {
        "retCode": 0,
        "result": {"list": []}  # Нет позиций
    }
    
    mock_bot = Mock()
    mock_bot.send_message = Mock()
    
    test_user_id = 99996
    users = {
        str(test_user_id): {
            "enabled": True,
            "api_key": "test_key",
            "api_secret": "test_secret",
            "leverage": 10,
            "margin": 20
        }
    }
    save_json(USERS_FILE, users)
    
    original_HTTP = trading_module.HTTP
    trading_module.HTTP = Mock(return_value=mock_session)
    
    try:
        trading_module.long_token("TEST", test_user_id, mock_bot)
        
        # Проверяем, что была вызвана проверка позиции
        assert mock_session.get_open_positions.called, "Проверка позиции не была вызвана"
        
        # Проверяем, что было отправлено предупреждение
        warning_calls = [call for call in mock_bot.send_message.call_args_list 
                       if "⚠️" in call[0][1] or "не обнаружена" in call[0][1]]
        assert len(warning_calls) > 0, "Предупреждение о позиции не отправлено"
        
        print("✅ Тест test_position_verification пройден")
    finally:
        trading_module.HTTP = original_HTTP


if __name__ == "__main__":
    print("Запуск тестов для улучшенной функции торговли...")
    
    # Создаем тестовые директории если их нет
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    
    try:
        test_order_retry_on_failure()
        test_order_check_result()
        test_order_failure_after_all_retries()
        test_position_verification()
        
        print("\n✅ Все тесты пройдены успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

