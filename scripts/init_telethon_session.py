#!/usr/bin/env python3
"""
Скрипт для первичной авторизации Telethon
Запустите один раз для создания сессии

Использование:
    cd /root/trade_bot
    source .venv/bin/activate
    python3 scripts/init_telethon_session.py
"""
import sys
import os

# Определяем корневую директорию проекта
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Добавляем src в путь
sys.path.insert(0, os.path.join(project_root, 'src'))

# Проверяем, что мы в виртуальном окружении
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    venv_path = os.path.join(project_root, '.venv')
    if os.path.exists(venv_path):
        print("⚠️  Виртуальное окружение не активировано!")
        print(f"   Выполните: source {venv_path}/bin/activate")
        print("   Или запустите: .venv/bin/python3 scripts/init_telethon_session.py")

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

