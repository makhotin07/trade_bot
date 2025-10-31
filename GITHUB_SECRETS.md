# GitHub Actions Secrets

Для автоматического деплоя добавьте следующие секреты в GitHub:

## Settings → Secrets and variables → Actions → New repository secret

### 1. SSH_PRIVATE_KEY
Содержимое файла `~/.ssh/id_github_actions`:

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
(весь файл полностью)
...
-----END OPENSSH PRIVATE KEY-----
```

**Как получить:**
```bash
cat ~/.ssh/id_github_actions
# Скопируйте ВСЁ содержимое файла
```

### 2. SERVER_HOST
```
91.229.8.171
```

### 3. SERVER_USER
```
root
```

### 4. SERVER_PATH
```
/root/trade_bot
```

---

## ✅ Проверка

После добавления секретов при пуше в `master`:
1. ✅ Запустится проверка линтеров
2. ✅ Запустятся тесты  
3. ✅ Автоматически выполнится `git pull` на сервере
4. ✅ Обновятся зависимости
5. ✅ Бот автоматически перезапустится

---

## Проверка на сервере

```bash
ssh root@91.229.8.171
cd /root/trade_bot
systemctl status bytbit-bot.service
journalctl -u bytbit-bot.service -n 50 -f
```

