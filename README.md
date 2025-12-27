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

Рекомендуемые значения для маленького системного диска:
- `DB_PATH=/data/apps/dcrm/db.sqlite3`
- `MEDIA_ROOT=/data/apps/dcrm/media`

### 3) Запуск через Docker Compose
```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
```

Открыть сайт: `http://<server-ip>:8000`

### 4) Если нужно перенести текущие данные (БД/загрузки)
Если на старой машине уже есть данные и их надо сохранить:
```bash
# Пример: копирование sqlite базы
cp /путь/до/старого/db.sqlite3 /data/apps/dcrm/db.sqlite3

# Пример: копирование загруженных файлов
rsync -a /путь/до/старого/media/uploads/ /data/apps/dcrm/media/uploads/
```


