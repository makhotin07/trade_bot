"""
Модуль торговли на Bybit
"""
import logging
from pybit.unified_trading import HTTP
from .utils import get_user_config, round_to_tick_size, round_to_qty_step
from .config import TP1_PCT, TP2_PCT, STOP_LOSS_PCT, BUY_PCT

logger = logging.getLogger(__name__)


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
        session.set_leverage(
            category="linear",
            symbol=token_symbol,
            buyLeverage=str(int(leverage)),
            sellLeverage=str(int(leverage)),
        )
        
        # Buy 70% with position SL
        session.place_order(
            category="linear",
            symbol=token_symbol,
            side="Buy",
            order_type="Market",
            qty=round(buy_qty, 0),
            reduce_only=False,
            time_in_force="GoodTillCancel",
            stopLoss=str(sl)  # явное преобразование в строку
        )
        
        # TP1 limit sell 40%
        if tp1_qty >= min_qty:
            session.place_order(
                category="linear",
                symbol=token_symbol,
                side="Sell",
                order_type="Limit",
                qty=round(tp1_qty, 0),
                price=str(tp1),  # явное преобразование в строку
                reduce_only=True,
                time_in_force="GoodTillCancel"
            )
        
        # TP2 limit sell 30%
        if tp2_qty >= min_qty:
            session.place_order(
                category="linear",
                symbol=token_symbol,
                side="Sell",
                order_type="Limit",
                qty=round(tp2_qty, 0),
                price=str(tp2),  # явное преобразование в строку
                reduce_only=True,
                time_in_force="GoodTillCancel"
            )
        
        bot.send_message(user_id, f"✅ Лонг по {token_symbol} выполнен по цене {price:.2f}")
        
    except Exception as err:
        logger.error(f'Error while placing order for {token}: {err}', exc_info=True)
        bot.send_message(user_id, f"❌ Ошибка выполнения ордера для {token}: {str(err)}")

