## dcrm

### Что делаем (коротко)
- **Пушим текущую версию в GitHub** (без `.env`, без `db.sqlite3`, без `media/uploads`).
- На сервере/Ubuntu **клонируем в `/data`** и поднимаем через Docker.

### Важно про секреты
- Файл `.env` **не должен попадать в git** (уже исключён в `.gitignore`).
- В репозитории лежит `env.example` — **скопируйте его в `.env`** и заполните.

### 1) Залить в GitHub (локально)
```bash
git init
git add -A
git commit -m "Initial commit"

# Создайте репозиторий на GitHub (лучше private) и добавьте remote:
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

### 2) Развернуть на Ubuntu в `/data`
```bash
sudo mkdir -p /data/apps
cd /data/apps
git clone <YOUR_GITHUB_REPO_URL> dcrm
cd dcrm

cp env.example .env
nano .env
```

Минимум, который стоит настроить в `.env`:
- `SECRET_KEY` (обязательно заменить на свой)
- (опционально) `TELEGRAM_BOT_TOKEN` если нужен tg-бот
- (опционально) `RESTIC_PASSWORD` если нужны бэкапы (пароль должен быть постоянным)

Пути по умолчанию (уже подходят для `/data/apps/dcrm`):
- `DB_PATH=/data/db.sqlite3`  → файл на диске `/data/apps/dcrm/db.sqlite3`
- `MEDIA_ROOT=/data/media`    → папка на диске `/data/apps/dcrm/media`

### 3) Запуск через Docker Compose
```bash
docker compose up -d --build
```

Открыть сайт:
- напрямую: `http://<server-ip>:8000`
- через reverse-proxy (Traefik): `http://<server-ip>:8088`
  - HTTPS: порт `443` (сертификаты лежат в `docker/certs`, динамический TLS конфиг — в `docker/traefik/dynamic`)

### TG-бот (опционально)
Бот запускается отдельным сервисом `bot` (профиль `bot`).
```bash
docker compose --profile bot up -d --build
docker compose logs -f --tail=100 bot
```

### Бэкапы (SQLite + media)
Проект может запускать сервис `backup`, который делает снапшоты `db.sqlite3` и `media` в restic-репозиторий:
- Папка на диске: `/data/apps/dcrm/backups`
- Внутри будет repo: `/data/apps/dcrm/backups/dcrm`

Запуск:
```bash
docker compose --profile backup up -d backup
docker compose logs -f --tail=100 backup
```

### 4) Если нужно перенести текущие данные (БД/загрузки)
Если на старой машине уже есть данные и их надо сохранить:
```bash
# Пример: копирование sqlite базы
cp /путь/до/старого/db.sqlite3 /data/apps/dcrm/db.sqlite3

# Пример: копирование загруженных файлов
rsync -a /путь/до/старого/media/uploads/ /data/apps/dcrm/media/uploads/
```


