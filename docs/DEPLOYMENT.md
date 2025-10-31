# GitHub Actions Secrets

Для работы CI/CD необходимо добавить следующие секреты в настройках репозитория GitHub:

1. `SSH_PRIVATE_KEY` - приватный SSH ключ для доступа к серверу
2. `SERVER_HOST` - IP адрес или домен сервера (требуется публичный IP или домен)
3. `SERVER_USER` - имя пользователя для SSH подключения
4. `SERVER_PATH` - полный путь к проекту на сервере

## ⚠️ Важно: Публичный IP

**Для автоматического деплоя из GitHub Actions нужен публичный IP или домен.**

Если у вас нет публичного IP:
- Используйте ручной деплой (см. ниже)
- Или используйте GitHub Self-hosted Runner
- Или настройте Cloudflare Tunnel / Reverse SSH

Подробнее см. `docs/NETWORK_REQUIREMENTS.md`

## Как добавить секреты:

1. Перейдите в Settings → Secrets and variables → Actions
2. Нажмите "New repository secret"
3. Добавьте каждый секрет с соответствующим именем и значением

## Как получить SSH ключ:

```bash
# Если у вас еще нет SSH ключа
ssh-keygen -t ed25519 -C "github-actions"

# Скопируйте приватный ключ
cat ~/.ssh/id_ed25519

# Добавьте публичный ключ на сервер
ssh-copy-id user@server
```

## Ручной деплой (если нет публичного IP):

Если автоматический деплой не работает, используйте ручной:

```bash
# Подключитесь к серверу
ssh user@server

# Перейдите в директорию проекта
cd /path/to/project

# Обновите код
git pull origin main

# Активируйте виртуальное окружение
source .venv/bin/activate

# Обновите зависимости
pip install -r requirements.txt --upgrade

# Перезапустите бота
sudo systemctl restart bytbit-bot.service
# или
bash scripts/restart.sh
```

