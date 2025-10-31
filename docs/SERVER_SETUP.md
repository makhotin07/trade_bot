# Инструкция по развертыванию на сервере

## Быстрое развертывание

### Вариант 1: Автоматическое развертывание (рекомендуется)

```bash
# Запустите скрипт развертывания с вашего компьютера
bash scripts/deploy_remote.sh
```

Этот скрипт автоматически:
- Подключится к серверу
- Установит все зависимости
- Клонирует репозиторий
- Настроит виртуальное окружение
- Установит зависимости Python

---

### Вариант 2: Ручное развертывание

#### Шаг 1: Подключитесь к серверу
```bash
ssh root@91.229.8.171
# Введите пароль: 6UbkBqwG4xZez36u
```

#### Шаг 2: Установите зависимости системы
```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv git
```

#### Шаг 3: Клонируйте репозиторий
```bash
cd /root
git clone https://github.com/makhotin07/trade_bot.git
cd trade_bot
```

#### Шаг 4: Создайте виртуальное окружение
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Шаг 5: Установите зависимости
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Шаг 6: Создайте директории для данных
```bash
mkdir -p src/bytbit_trading_bot/data
echo "{}" > src/bytbit_trading_bot/data/users.json
echo "{}" > src/bytbit_trading_bot/data/tokens.json
```

#### Шаг 7: Настройте конфигурацию
```bash
# Отредактируйте config.py или установите переменные окружения
nano src/bytbit_trading_bot/config.py
```

#### Шаг 8: Запустите бота
```bash
# Запуск напрямую
python main.py

# Или через systemd (для автозапуска)
sudo cp scripts/bytbit-bot.service /etc/systemd/system/
sudo nano /etc/systemd/system/bytbit-bot.service  # Отредактируйте пути
sudo systemctl daemon-reload
sudo systemctl enable bytbit-bot.service
sudo systemctl start bytbit-bot.service
```

---

## Настройка SSH ключей для автоматического деплоя

### Шаг 1: Создайте SSH ключ
```bash
# На вашем компьютере
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/id_github_actions
```

### Шаг 2: Добавьте публичный ключ на сервер
```bash
# Скопируйте публичный ключ на сервер
ssh-copy-id -i ~/.ssh/id_github_actions.pub root@91.229.8.171
# Введите пароль: 6UbkBqwG4xZez36u
```

### Шаг 3: Проверьте подключение без пароля
```bash
ssh -i ~/.ssh/id_github_actions root@91.229.8.171
# Должно подключиться без пароля
```

### Шаг 4: Добавьте приватный ключ в GitHub Secrets
```bash
# Скопируйте приватный ключ
cat ~/.ssh/id_github_actions

# Добавьте в GitHub:
# Settings → Secrets and variables → Actions → New repository secret
# Name: SSH_PRIVATE_KEY
# Value: (вставьте весь приватный ключ)
```

### Шаг 5: Настройте другие секреты в GitHub
- `SERVER_HOST` = `91.229.8.171`
- `SERVER_USER` = `root`
- `SERVER_PATH` = `/root/trade_bot`

---

## Настройка systemd для автозапуска

### Отредактируйте service файл
```bash
sudo nano /etc/systemd/system/bytbit-bot.service
```

Измените пути:
```ini
[Unit]
Description=Bybit Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/trade_bot
Environment="PATH=/root/trade_bot/.venv/bin"
ExecStart=/root/trade_bot/.venv/bin/python /root/trade_bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Активируйте сервис
```bash
sudo systemctl daemon-reload
sudo systemctl enable bytbit-bot.service
sudo systemctl start bytbit-bot.service

# Проверка статуса
sudo systemctl status bytbit-bot.service

# Просмотр логов
sudo journalctl -u bytbit-bot.service -f
```

---

## Проверка работы

### Проверка подключения
```bash
ssh root@91.229.8.171
```

### Проверка статуса бота
```bash
# Если запущен через systemd
sudo systemctl status bytbit-bot.service

# Или проверьте процессы
ps aux | grep python
```

### Просмотр логов
```bash
# systemd логи
sudo journalctl -u bytbit-bot.service -n 100 -f

# Или если запущен напрямую
tail -f bot.log
```

---

## Обновление проекта

### Ручное обновление
```bash
ssh root@91.229.8.171
cd /root/trade_bot
git pull origin master
source .venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart bytbit-bot.service
```

### Автоматическое обновление
После настройки GitHub Secrets, при пуше в `master` автоматически запустится деплой.

