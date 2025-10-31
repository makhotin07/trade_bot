# Инструкция по развертыванию

## Первоначальная настройка сервера (один раз)

### 1. Подключитесь к серверу:
```bash
ssh root@91.229.8.171
# Пароль: 6UbkBqwG4xZez36u
```

### 2. Выполните на сервере:
```bash
# Установка зависимостей
apt-get update && apt-get install -y python3 python3-pip python3-venv git

# Клонирование проекта
cd /root
git clone https://github.com/makhotin07/trade_bot.git
cd trade_bot

# Запуск скрипта настройки
bash scripts/setup_server.sh
```

### 3. Настройте конфигурацию:
```bash
nano src/bytbit_trading_bot/config.py
# Проверьте API ключи
```

### 4. Запустите бота:
```bash
systemctl start bytbit-bot.service
systemctl status bytbit-bot.service
```

---

## Настройка автоматического деплоя из GitHub

### 1. Создайте SSH ключ для GitHub Actions:
```bash
# На вашем компьютере
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/id_github_actions
```

### 2. Добавьте публичный ключ на сервер:
```bash
ssh-copy-id -i ~/.ssh/id_github_actions.pub root@91.229.8.171
# Введите пароль: 6UbkBqwG4xZez36u
```

### 3. Добавьте секреты в GitHub:
Перейдите: `Settings → Secrets and variables → Actions`

Добавьте:
- **SSH_PRIVATE_KEY**: содержимое `~/.ssh/id_github_actions` (весь файл)
- **SERVER_HOST**: `91.229.8.171`
- **SERVER_USER**: `root`
- **SERVER_PATH**: `/root/trade_bot`

---

## Готово! 

Теперь при каждом пуше в `master`:
1. ✅ Запустится проверка линтеров
2. ✅ Запустятся тесты
3. ✅ Код автоматически обновится на сервере
4. ✅ Бот автоматически перезапустится

---

## Проверка

После пуша проверьте GitHub Actions:
- Перейдите в `Actions` в репозитории
- Посмотрите последний workflow run

Проверьте статус на сервере:
```bash
ssh root@91.229.8.171
systemctl status bytbit-bot.service
journalctl -u bytbit-bot.service -n 50 -f
```
