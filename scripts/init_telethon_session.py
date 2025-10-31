#!/usr/bin/env python3
"""
Скрипт для первичной авторизации Telethon
Запустите один раз для создания сессии

Использование:
    cd /root/trade_bot
    source .venv/bin/activate
    python3 scripts/init_telethon_session.py
    
    Или напрямую:
    .venv/bin/python3 scripts/init_telethon_session.py
"""
import sys
import os
import asyncio

# Определяем корневую директорию проекта
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Добавляем src в путь
sys.path.insert(0, os.path.join(project_root, 'src'))

from telethon import TelegramClient
from bytbit_trading_bot.config import API_ID, API_HASH, SESSION_NAME, CHANNEL


async def init_telethon_session():
    """
    Инициализирует Telethon сессию через интерактивный ввод
    """
    if not API_ID or not API_HASH:
        print("❌ Ошибка: API_ID или API_HASH не настроены в config.py")
        return
    
    print("=" * 60)
    print("🔐 Авторизация Telethon")
    print("=" * 60)
    print("Этот скрипт нужно запустить ОДИН РАЗ для создания сессии.")
    print("После успешной авторизации сессия будет сохранена в файл my_session.session")
    print("")
    print("⚠️  ВАЖНО: Для чтения истории сообщений нужна авторизация через НОМЕР ТЕЛЕФОНА!")
    print("   При запросе 'Please enter your phone (or bot token):'")
    print("   Введите НОМЕР ТЕЛЕФОНА (например: +79991234567), а НЕ токен бота!")
    print("   Токен бота не позволяет читать историю сообщений из канала.")
    print("=" * 60)
    print("")
    
    # Создаём клиент
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Подключаемся и запускаем интерактивную авторизацию через номер телефона
        await client.start()
        
        # Проверяем, что авторизация прошла как пользователь
        me = await client.get_me()
        
        if me.bot:
            print("❌ ОШИБКА: Авторизация прошла как бот!")
            print("   Удалите файл my_session.session и попробуйте снова")
            print("   При запросе введите НОМЕР ТЕЛЕФОНА, а не токен бота!")
            return
        
        print(f"\n✅ Успешно авторизован как пользователь: {me.first_name} (@{me.username})")
        print(f"📱 Тест подключения к каналу {CHANNEL}...")
        
        # Проверяем доступ к каналу
        try:
            entity = await client.get_entity(CHANNEL)
            print(f"✅ Канал доступен: {entity.title}")
        except Exception as e:
            print(f"⚠️  Не удалось получить доступ к каналу: {e}")
        
        print("\n✅ Сессия успешно создана и сохранена!")
        print("   Теперь можно запускать бота через systemd:")
        print("   systemctl start bytbit-bot.service")
        
    except KeyboardInterrupt:
        print("\n\n✅ Сессия сохранена. Теперь можно запускать бота через systemd.")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # Проверяем, что мы в виртуальном окружении
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        venv_path = os.path.join(project_root, '.venv')
        if os.path.exists(venv_path):
            print("⚠️  Виртуальное окружение не активировано!")
            print(f"   Выполните: source {venv_path}/bin/activate")
            print("   Или запустите: .venv/bin/python3 scripts/init_telethon_session.py")
            print("")
    
    try:
        asyncio.run(init_telethon_session())
    except KeyboardInterrupt:
        print("\n\n✅ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)

