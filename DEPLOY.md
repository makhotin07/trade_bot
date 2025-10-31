# Быстрое развертывание на сервер

## 🚀 Развертывание за 3 шага

### 1. Запустите автоматический скрипт развертывания:

```bash
bash scripts/deploy_remote.sh
```

Этот скрипт автоматически развернет проект на сервере `91.229.8.171`.

---

### 2. Или разверните вручную (если автоматический не работает):

**Подключитесь к серверу:**
```bash
ssh root@91.229.8.171
# Пароль: 6UbkBqwG4xZez36u
```

**Выполните на сервере:**
```bash
# Установка зависимостей
apt-get update && apt-get install -y python3 python3-pip python3-venv git

# Клонирование проекта
cd /root
git clone https://github.com/makhotin07/trade_bot.git
cd trade_bot

# Настройка окружения
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Создание директорий для данных
mkdir -p src/bytbit_trading_bot/data
echo "{}" > src/bytbit_trading_bot/data/users.json
echo "{}" > src/bytbit_trading_bot/data/tokens.json
```

---

### 3. Настройте и запустите бота:

**На сервере:**
```bash
# Настройте config.py (отредактируйте API ключи)
nano src/bytbit_trading_bot/config.py

# Запустите бота (для теста)
python main.py

# Или настройте автозапуск через systemd
sudo cp scripts/bytbit-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bytbit-bot.service
sudo systemctl start bytbit-bot.service

# Проверка статуса
sudo systemctl status bytbit-bot.service
```

---

## 📝 Настройка SSH ключей для автоматического деплоя

Для работы автоматического деплоя из GitHub Actions:

```bash
# 1. Создайте SSH ключ
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/id_github_actions

# 2. Добавьте публичный ключ на сервер
ssh-copy-id -i ~/.ssh/id_github_actions.pub root@91.229.8.171

# 3. Добавьте приватный ключ в GitHub Secrets
cat ~/.ssh/id_github_actions
# Скопируйте содержимое и добавьте в GitHub:
# Settings → Secrets → SSH_PRIVATE_KEY

# 4. Добавьте другие секреты:
# SERVER_HOST = 91.229.8.171
# SERVER_USER = root
# SERVER_PATH = /root/trade_bot
```

Подробнее: `docs/SERVER_SETUP.md`

