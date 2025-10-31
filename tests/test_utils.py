import pytest
import sys
import os

# Добавляем src в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bytbit_trading_bot.utils import parse_result_date, round_to_tick_size, round_to_qty_step


def test_parse_result_date():
    """Тест парсинга даты"""
    # Тест с UTC
    date_utc = parse_result_date("14.11.2025 11:00 UTC")
    assert date_utc is not None
    
    # Тест без UTC
    date_no_utc = parse_result_date("14.11.2025 11:00")
    assert date_no_utc is not None


def test_round_to_tick_size():
    """Тест округления до шага цены"""
    assert round_to_tick_size(100.123, 0.01) == 100.12
    assert round_to_tick_size(100.129, 0.01) == 100.12
    assert round_to_tick_size(100.125, 0.01) == 100.12


def test_round_to_qty_step():
    """Тест округления до шага объёма"""
    assert round_to_qty_step(100.5, 1) == 100.0
    assert round_to_qty_step(100.7, 1) == 100.0
    assert round_to_qty_step(100.3, 1) == 100.0

