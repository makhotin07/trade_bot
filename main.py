#!/usr/bin/env python3
"""
Точка входа для запуска бота
"""
import sys
import os

# Добавляем src в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bytbit_trading_bot.main import main

if __name__ == "__main__":
    main()
