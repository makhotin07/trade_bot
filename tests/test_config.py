import pytest
from bytbit_trading_bot.config import POST_REGEX
import re


def test_post_regex():
    """Тест регулярного выражения для парсинга сообщений"""
    # Тест с UTC
    message_utc = "RECALL\nStart 31.10.2025 10:00 UTC\nResult 14.11.2025 11:00 UTC"
    match = re.match(POST_REGEX, message_utc, re.DOTALL | re.MULTILINE)
    assert match is not None
    assert match.group("token") == "RECALL"
    assert match.group("result_date") == "14.11.2025 11:00 UTC"
    
    # Тест без UTC
    message_no_utc = "LA\nToken Splash Event\nResult 31.10.2024 15:30"
    match = re.match(POST_REGEX, message_no_utc, re.DOTALL | re.MULTILINE)
    assert match is not None
    assert match.group("token") == "LA"
    assert match.group("result_date") == "31.10.2024 15:30"

