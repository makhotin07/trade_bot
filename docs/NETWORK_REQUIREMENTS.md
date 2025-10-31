# Сетевые требования для Bybit Trading Bot

## Нужен ли публичный IP адрес?

### Для работы бота: ❌ НЕ ОБЯЗАТЕЛЬНО

**Бот работает через исходящие соединения:**

1. **Telegram Bot API** (`api.telegram.org`)
   - Бот инициирует HTTPS соединения
   - Достаточно исходящего интернета
   - Не нужен публичный IP

2. **Telethon** (Telegram MTProto)
   - Инициирует исходящие соединения к серверам Telegram
   - Достаточно исходящего интернета
   - Не нужен публичный IP

3. **Bybit API** (`api.bybit.com`)
   - Инициирует HTTPS запросы
   - Достаточно исходящего интернета
   - Не нужен публичный IP

**Вывод:** Для работы бота достаточно **исходящего интернета**. Публичный IP не требуется.

---

### Для автоматического деплоя (CI/CD): ✅ ЖЕЛАТЕЛЬНО

**GitHub Actions нужен SSH доступ к серверу:**

1. **Автоматический деплой** через GitHub Actions
   - Требует SSH подключения к серверу
   - **Нужен публичный IP или домен**

2. **Альтернативы без публичного IP:**
   - Ручной деплой через SSH с вашего компьютера
   - Использование GitHub Self-hosted Runner
   - VPN туннель или Cloudflare Tunnel
   - Reverse SSH туннель

---

## Варианты настройки

### Вариант 1: С публичным IP (рекомендуется) ✅

**Преимущества:**
- Автоматический деплой из GitHub Actions
- Простая настройка
- Легкий доступ для отладки

**Настройка:**
1. Настройте firewall (откройте порт 22 для SSH):
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

2. Настройте SSH ключи:
   ```bash
   # На GitHub Actions сервере
   ssh-keygen -t ed25519 -C "github-actions"
   
   # Добавьте публичный ключ на сервер
   ssh-copy-id user@your-server-ip
   ```

3. Добавьте секреты в GitHub:
   - `SERVER_HOST` = ваш публичный IP или домен
   - `SERVER_USER` = пользователь для SSH
   - `SERVER_PATH` = путь к проекту
   - `SSH_PRIVATE_KEY` = приватный ключ

---

### Вариант 2: Без публичного IP (ручной деплой)

**Если у вас нет публичного IP:**

1. **Ручной деплой:**
   ```bash
   # На вашем компьютере
   ssh user@internal-ip
   cd /path/to/project
   git pull origin main
   source .venv/bin/activate
   pip install -r requirements.txt --upgrade
   sudo systemctl restart bytbit-bot.service
   ```

2. **Или используйте GitHub Self-hosted Runner:**
   - Установите runner на сервере
   - Деплой будет происходить локально
   - Не нужен публичный IP

---

### Вариант 3: Cloudflare Tunnel (без публичного IP)

**Используйте Cloudflare Tunnel для SSH:**

1. Установите cloudflared на сервере:
   ```bash
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
   chmod +x cloudflared-linux-amd64
   sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
   ```

2. Создайте туннель:
   ```bash
   cloudflared tunnel create bytbit-bot
   cloudflared tunnel route dns bytbit-bot ssh.yourdomain.com
   ```

3. Настройте config:
   ```yaml
   tunnel: bytbit-bot
   ingress:
     - hostname: ssh.yourdomain.com
       service: ssh://localhost:22
   ```

4. В GitHub Actions используйте домен вместо IP:
   - `SERVER_HOST` = `ssh.yourdomain.com`

---

### Вариант 4: Reverse SSH Tunnel

**Создайте обратный SSH туннель:**

1. На сервере (без публичного IP):
   ```bash
   # Подключитесь к промежуточному серверу с публичным IP
   ssh -R 2222:localhost:22 user@intermediate-server.com
   ```

2. В GitHub Actions:
   - `SERVER_HOST` = `intermediate-server.com`
   - Подключение через порт 2222

---

## Рекомендации

### Для продакшена:
- ✅ **Используйте публичный IP** для автоматического деплоя
- ✅ **Настройте firewall** (только SSH, закрыть все остальное)
- ✅ **Используйте SSH ключи** вместо паролей
- ✅ **Отключите root доступ** по SSH

### Безопасность:
```bash
# Настройка SSH
sudo nano /etc/ssh/sshd_config

# Измените:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # Измените стандартный порт

# Перезапустите SSH
sudo systemctl restart sshd
```

### Если нет публичного IP:
- Используйте **ручной деплой** или **Self-hosted Runner**
- Бот будет работать нормально (ему не нужен публичный IP)
- Автоматический деплой из GitHub Actions будет недоступен

---

## Итоговый ответ

**Для работы бота:** ❌ Публичный IP **НЕ НУЖЕН**
- Достаточно исходящего интернета
- Бот инициирует все соединения сам

**Для автоматического деплоя:** ✅ Публичный IP **ЖЕЛАТЕЛЕН**
- Для работы CI/CD из GitHub Actions
- Можно обойтись ручным деплоем или Self-hosted Runner

**Вывод:** Если у вас нет публичного IP - бот будет работать нормально, но автоматический деплой из GitHub Actions не будет работать. Можно использовать ручной деплой или альтернативные решения.

