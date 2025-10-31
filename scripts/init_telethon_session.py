#!/usr/bin/env python3
"""
Скрипт для первичной авторизации Telethon
Запустите один раз для создания сессии
"""
import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
from bytbit_trading_bot.parser import start_telethon

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Авторизация Telethon")
    print("=" * 60)
    print("Этот скрипт нужно запустить ОДИН РАЗ для создания сессии.")
    print("После успешной авторизации сессия будет сохранена в файл my_session.session")
    print("")
    print("⚠️  ВАЖНО: При запросе 'Please enter your phone (or bot token):'")
    print("   Введите НОМЕР ТЕЛЕФОНА (например: +79991234567), а НЕ токен бота!")
    print("=" * 60)
    print("")
    
    try:
        asyncio.run(start_telethon())
    except KeyboardInterrupt:
        print("\n\n✅ Сессия сохранена. Теперь можно запускать бота через systemd.")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)

