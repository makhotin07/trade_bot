"""
Модуль торговли на Bybit
"""
import logging
import time
from pybit.unified_trading import HTTP
from .utils import get_user_config, round_to_tick_size, round_to_qty_step
from .config import TP1_PCT, TP2_PCT, STOP_LOSS_PCT, BUY_PCT

logger = logging.getLogger(__name__)

# Максимальное количество попыток размещения ордера
MAX_RETRIES = 3
RETRY_DELAY = 2  # секунды между попытками


def get_balance(user_id, bot):
    """
    Получает текущий баланс счета на Bybit
    
    Args:
        user_id: ID пользователя Telegram
        bot: Экземпляр Telegram бота
    """
    try:
        user_config = get_user_config(user_id)
        
        if not user_config.get("api_key") or not user_config.get("api_secret"):
            bot.send_message(user_id, "❌ Не настроены API ключи Bybit")
            return
        
        api_key = user_config["api_key"]
        api_secret = user_config["api_secret"]
        
        session = HTTP(
            testnet=False,
            api_key=api_key,
            api_secret=api_secret,
        )
        
        # Получаем баланс Unified Trading Account
        balance_response = session.get_wallet_balance(
            accountType="UNIFIED",
            coin="USDT",
        )
        
        if balance_response.get("retCode") != 0:
            error_msg = balance_response.get("retMsg", "Unknown error")
            bot.send_message(user_id, f"❌ Ошибка получения баланса: {error_msg}")
            logger.error(f"[Trading] Ошибка получения баланса: {error_msg}")
            return
        
        result = balance_response.get("result", {})
        if not result.get("list"):
            bot.send_message(user_id, "❌ Данные баланса не найдены")
            return
        
        account = result["list"][0]
        coin_list = account.get("coin", [])
        
        if not coin_list:
            bot.send_message(user_id, "❌ Информация о монетах не найдена")
            return
        
        # Формируем сообщение с балансом
        balance_text = "💰 Текущий баланс:\n\n"
        
        for coin in coin_list:
            coin_name = coin.get("coin", "N/A")
            wallet_balance = float(coin.get("walletBalance", 0))
            available_balance = float(coin.get("availableToWithdraw", 0))
            locked = float(coin.get("locked", 0))
            
            if wallet_balance > 0 or locked > 0:
                balance_text += (
                    f"**{coin_name}**\n"
                    f"Доступно: {wallet_balance:.4f}\n"
                    f"Заблокировано: {locked:.4f}\n"
                    f"Доступно к выводу: {available_balance:.4f}\n\n"
                )
        
        # Если нет баланса, показываем только USDT
        if "USDT" not in balance_text:
            usdt_coin = next((c for c in coin_list if c.get("coin") == "USDT"), None)
            if usdt_coin:
                wallet_balance = float(usdt_coin.get("walletBalance", 0))
                available_balance = float(usdt_coin.get("availableToWithdraw", 0))
                locked = float(usdt_coin.get("locked", 0))
                
                balance_text = (
                    f"💰 Баланс USDT:\n\n"
                    f"Доступно: {wallet_balance:.4f} USDT\n"
                    f"Заблокировано: {locked:.4f} USDT\n"
                    f"Доступно к выводу: {available_balance:.4f} USDT"
                )
            else:
                balance_text = "💰 Баланс USDT: 0.0000 USDT"
        
        bot.send_message(user_id, balance_text, parse_mode='Markdown')
        logger.info(f"[Trading] Баланс успешно получен для пользователя {user_id}")
        
    except Exception as err:
        logger.error(f'Error while getting balance for user {user_id}: {err}', exc_info=True)
        bot.send_message(user_id, f"❌ Ошибка получения баланса: {str(err)}")


def long_token(token, user_id, bot):
    """
    Открывает длинную позицию по токену
    
    Args:
        token: Символ токена (например, LAUSDT)
        user_id: ID пользователя Telegram
        bot: Экземпляр Telegram бота
    """
    try:
        user_config = get_user_config(user_id)
        
        if not user_config.get("api_key") or not user_config.get("api_secret"):
            bot.send_message(user_id, "❌ Не настроены API ключи Bybit")
            return
        
        api_key = user_config["api_key"]
        api_secret = user_config["api_secret"]
        leverage = float(user_config.get("leverage", 10))
        margin = float(user_config.get("margin", 20))
        
        session = HTTP(
            testnet=False,
            api_key=api_key,
            api_secret=api_secret,
        )
        
        # Формируем символ токена (добавляем USDT если его нет)
        token = token.upper()
        if token.endswith("USDT"):
            token_symbol = token
        else:
            token_symbol = f"{token}USDT"
        
        # Получаем информацию об инструменте
        instrument_info = session.get_instruments_info(
            category="linear",
            symbol=token_symbol,
        )
        
        if instrument_info.get("retCode") != 0:
            bot.send_message(user_id, f"❌ Ошибка получения информации об инструменте: {instrument_info.get('retMsg')}")
            return
        
        result = instrument_info.get("result", {})
        if not result.get("list"):
            bot.send_message(user_id, f"❌ Инструмент {token_symbol} не найден")
            return
        
        instrument = result["list"][0]
        tick_size = float(instrument.get("tickSize", "0.01"))
        qty_step = float(instrument.get("lotSizeFilter", {}).get("qtyStep", "1"))
        min_qty = float(instrument.get("lotSizeFilter", {}).get("minQty", "1"))
        
        # Получаем текущую цену
        ticker = session.get_tickers(
            category="linear",
            symbol=token_symbol,
        )
        
        if ticker.get("retCode") != 0 or not ticker.get("result", {}).get("list"):
            bot.send_message(user_id, f"❌ Ошибка получения цены для {token_symbol}")
            return
        
        price = float(ticker["result"]["list"][0]["lastPrice"])
        
        # Рассчитываем объём
        raw_qty = (leverage * margin) / price
        qty = round_to_qty_step(raw_qty, qty_step)
        
        if qty < min_qty:
            bot.send_message(user_id, f"❌ Рассчитанный объём {qty} меньше минимального {min_qty}")
            return
        
        # Проверяем баланс
        balance = session.get_wallet_balance(
            accountType="UNIFIED",
            coin="USDT",
        )
        
        if balance.get("retCode") != 0:
            bot.send_message(user_id, "❌ Ошибка получения баланса")
            return
        
        available_balance = float(balance["result"]["list"][0]["coin"][0]["walletBalance"])
        
        if available_balance < margin:
            bot.send_message(user_id, f"❌ Недостаточно средств. Доступно: {available_balance} USDT, требуется: {margin} USDT")
            return
        
        # Рассчитываем цены TP и SL
        tp1 = round_to_tick_size(price * (1 + TP1_PCT / 100), tick_size)
        tp2 = round_to_tick_size(price * (1 + TP2_PCT / 100), tick_size)
        sl = round_to_tick_size(price * (1 - STOP_LOSS_PCT / 100), tick_size)
        
        # Рассчитываем объёмы
        buy_qty = qty * (BUY_PCT / 100)
        buy_qty = round_to_qty_step(buy_qty, qty_step)
        
        tp1_qty = buy_qty * 0.4  # 40% от позиции
        tp1_qty = round_to_qty_step(tp1_qty, qty_step)
        
        tp2_qty = buy_qty * 0.3  # 30% от позиции
        tp2_qty = round_to_qty_step(tp2_qty, qty_step)
        
        sl_qty = buy_qty * 0.3  # 30% от позиции для стоп-лосса
        
        logger.info(f"Размещение ордеров: buy={buy_qty}, tp1={tp1_qty}@{tp1}, tp2={tp2_qty}@{tp2}, sl={sl_qty}@{sl}")
        
        # Устанавливаем плечо
        leverage_result = session.set_leverage(
            category="linear",
            symbol=token_symbol,
            buyLeverage=str(int(leverage)),
            sellLeverage=str(int(leverage)),
        )
        
        if leverage_result.get("retCode") != 0:
            error_msg = f"❌ Ошибка установки плеча: {leverage_result.get('retMsg', 'Unknown error')}"
            logger.error(f"[Trading] {error_msg}")
            bot.send_message(user_id, error_msg)
            return
        
        # Размещаем основной ордер покупки с повторными попытками
        buy_order_id = None
        buy_order_success = False
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"[Trading] Попытка {attempt + 1}/{MAX_RETRIES} размещения ордера покупки для {token_symbol}")
                
                buy_order = session.place_order(
                    category="linear",
                    symbol=token_symbol,
                    side="Buy",
                    order_type="Market",
                    qty=round(buy_qty, 0),
                    reduce_only=False,
                    time_in_force="GoodTillCancel",
                    stopLoss=str(sl)
                )
                
                if buy_order.get("retCode") == 0:
                    buy_order_id = buy_order.get("result", {}).get("orderId")
                    buy_order_success = True
                    logger.info(f"[Trading] ✅ Ордер покупки размещен успешно. Order ID: {buy_order_id}")
                    break
                else:
                    error_msg = buy_order.get("retMsg", "Unknown error")
                    logger.warning(f"[Trading] Попытка {attempt + 1} неудачна: {error_msg}")
                    
                    # Если это последняя попытка, отправляем ошибку
                    if attempt == MAX_RETRIES - 1:
                        error_message = f"❌ Не удалось разместить ордер покупки после {MAX_RETRIES} попыток: {error_msg}"
                        bot.send_message(user_id, error_message)
                        return
                    else:
                        time.sleep(RETRY_DELAY)
                        
            except Exception as e:
                logger.error(f"[Trading] Исключение при попытке {attempt + 1}: {e}", exc_info=True)
                if attempt == MAX_RETRIES - 1:
                    error_message = f"❌ Критическая ошибка при размещении ордера: {str(e)}"
                    bot.send_message(user_id, error_message)
                    return
                time.sleep(RETRY_DELAY)
        
        if not buy_order_success:
            logger.error(f"[Trading] Не удалось разместить ордер покупки после всех попыток")
            bot.send_message(user_id, f"❌ Не удалось разместить ордер покупки для {token_symbol}")
            return
        
        # Проверяем, что позиция действительно открылась
        time.sleep(1)  # Даём время на обработку ордера
        
        try:
            positions = session.get_open_positions(
                category="linear",
                symbol=token_symbol,
            )
            
            if positions.get("retCode") == 0:
                position_list = positions.get("result", {}).get("list", [])
                position_found = any(
                    pos.get("symbol") == token_symbol and 
                    float(pos.get("size", 0)) > 0 
                    for pos in position_list
                )
                
                if not position_found:
                    logger.warning(f"[Trading] Позиция {token_symbol} не найдена после размещения ордера")
                    bot.send_message(
                        user_id,
                        f"⚠️ Ордер {token_symbol} размещен, но позиция не обнаружена. Проверьте вручную."
                    )
        except Exception as e:
            logger.error(f"[Trading] Ошибка проверки позиции: {e}", exc_info=True)
            # Не блокируем выполнение, продолжаем размещать TP ордера
        
        # Размещаем TP ордера
        tp_orders_placed = []
        
        # TP1 limit sell 40%
        if tp1_qty >= min_qty:
            try:
                tp1_order = session.place_order(
                    category="linear",
                    symbol=token_symbol,
                    side="Sell",
                    order_type="Limit",
                    qty=round(tp1_qty, 0),
                    price=str(tp1),
                    reduce_only=True,
                    time_in_force="GoodTillCancel"
                )
                
                if tp1_order.get("retCode") == 0:
                    tp_orders_placed.append(f"TP1@{tp1}")
                    logger.info(f"[Trading] ✅ TP1 ордер размещен успешно")
                else:
                    logger.warning(f"[Trading] ⚠️ TP1 ордер не размещен: {tp1_order.get('retMsg')}")
            except Exception as e:
                logger.error(f"[Trading] Ошибка размещения TP1: {e}", exc_info=True)
        
        # TP2 limit sell 30%
        if tp2_qty >= min_qty:
            try:
                tp2_order = session.place_order(
                    category="linear",
                    symbol=token_symbol,
                    side="Sell",
                    order_type="Limit",
                    qty=round(tp2_qty, 0),
                    price=str(tp2),
                    reduce_only=True,
                    time_in_force="GoodTillCancel"
                )
                
                if tp2_order.get("retCode") == 0:
                    tp_orders_placed.append(f"TP2@{tp2}")
                    logger.info(f"[Trading] ✅ TP2 ордер размещен успешно")
                else:
                    logger.warning(f"[Trading] ⚠️ TP2 ордер не размещен: {tp2_order.get('retMsg')}")
            except Exception as e:
                logger.error(f"[Trading] Ошибка размещения TP2: {e}", exc_info=True)
        
        # Формируем итоговое сообщение
        tp_info = f", размещены TP: {', '.join(tp_orders_placed)}" if tp_orders_placed else ""
        success_message = (
            f"✅ Лонг по {token_symbol} выполнен\n"
            f"Цена входа: {price:.4f} USDT\n"
            f"Объём: {buy_qty:.2f} {token_symbol.replace('USDT', '')}\n"
            f"SL: {sl:.4f} USDT{tp_info}"
        )
        
        bot.send_message(user_id, success_message)
        
    except Exception as err:
        logger.error(f'Error while placing order for {token}: {err}', exc_info=True)
        bot.send_message(user_id, f"❌ Ошибка выполнения ордера для {token}: {str(err)}")

