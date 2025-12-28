# AI Context / Аннотация проекта `dcrm`

Этот файл — краткая “памятка” для ИИ/разработчика, чтобы быстро восстановить контекст проекта без долгих раскопок.

## Что это за проект
- **Стек**: Django 5.2 + SQLite (`db.sqlite3`) + Docker Compose.
- **Основное Django-приложение**: `website`.
- **Хранилища на диске (host)**:
  - `./db.sqlite3` (SQLite БД)
  - `./media/` (загруженные файлы)
- **Запуск**: через `docker compose up -d --build` (миграции выполняются в entrypoint).

## Ключевые сущности (доменные модели)
Файл: `website/models.py`

- **Заказ/запись**: `Record`
  - финансы: `advance` (аванс), `contract_amount` (сумма договора), `delivery_price`, `workshop_price`
  - статусы: `Record.STATUS_CHOICES`
  - участники (работники): `designer`, `designer_worker`, `assembler_worker` (все — `Designer`)
  - связи:
    - `products = ManyToMany(Product)` (комплектующие)
    - детальная таблица связей: `RecordProduct` (quantity/custom_price/buyer)

- **Позиции в заказе**: `RecordProduct`
  - `quantity` (int)
  - `custom_price` (Decimal, опционально) — цена на момент/для этого заказа (если не задано, берётся `Product.our_price`)
  - `buyer` (Юра/Олег) — “кто купил”

- **Продукт**: `Product`
  - `our_price`, `parsed_price`, `source_url`, `image`
  - характеристики:
    - `custom_fields` (JSONField) — значения полей категории (по ключам `CategoryField.field_key`)
    - `ProductCustomField` — индивидуальные характеристики (объекты, привязанные к шаблонам `CategoryField`)

- **Категория и шаблоны полей**: `Category`, `CategoryField`

- **Работник**: `Designer`
  - `profession` (модель `Profession`) — используется для прав/отображения
  - `method` (модель `CalculationMethod`) + `percentage`/`rate_per_square_meter` — расчёты зарплат

- **Профиль пользователя**: `Profile`
  - связывает `User` и `Designer` (если назначен работник)
  - если `profile.designer` пустой и user не staff → это “заказчик”

## Важные страницы/вьюхи (где что реализовано)
- `website/views/auth.py`: главная страница + логин/логаут/регистрация.
  - **Важно**: редирект на `/accounts/login/` вернёт **404**, логин реализован на главной.
- `website/views/records.py`: создание/редактирование заказа, детальная страница заказа (`record_detail`).
- `website/views/products.py`: добавление товаров в заказ (`add_products_to_record`), список/детали продуктов.
- `website/views/payments.py`: расчёты/выплаты работникам (`WorkerPayment`).
- URL-роуты: `website/urls.py`, корневые: `dcrm/urls.py`.

## Docker / Compose
Файл: `docker-compose.yml`

Сервисы:
- `web`: Django (entrypoint делает `migrate` и запускает runserver)
- `proxy`: Traefik
- `selenium`: Selenium Chrome (опционально)
- `ufaloft`: watcher (опционально)
- `bot`: Telegram bot (опционально)
- `backup`: restic бэкап (профиль `backup`)
- `backup_orders`: частые “версии” БД (профиль `backup_orders`)

### Важно про `/data`
В контейнеры монтируются:
- `./db.sqlite3` → `/data/db.sqlite3`
- `./media` → `/data/media`

**Грабли**: если удалить `db.sqlite3` и поднять compose, Docker может создать **директорию** `db.sqlite3` вместо файла. Правильный сброс:
1) остановить `web` (и сервисы, которые читают БД),
2) сделать `: > db.sqlite3` (пустой файл),
3) поднять docker снова.

В `Dockerfile` создана директория `/data`, чтобы bind-mount файла в `/data/db.sqlite3` работал стабильно.

## Scheduler / фоновые задачи
Файл: `website/apps.py`

- APScheduler может запускаться в `ready()`.
- Чтобы **не стартовать фоновые процессы** (например, при разовых командах/миграциях/тестах), используется защита:
  - если `DJANGO_DISABLE_SCHEDULER=1` → scheduler не стартует
  - если `test` в argv → scheduler не стартует

## Бэкапы (restic)
Скрипты внутри образа `backup`:
- `/backup/run_backup_sqlite.sh` — архивный: DB + media, `restic forget --prune` по daily/weekly/monthly
- `/backup/run_restore_check_sqlite.sh` — проверка восстановления/целостности SQLite

### Архивный репозиторий (backup)
- репо: `${RESTIC_REPOSITORY:-/restic/dcrm}`
- ежедневный cron (EOD): `BACKUP_CRON` (дефолт 23:05 UTC)
- retention:
  - `RETENTION_KEEP_DAILY` (дефолт 30)
  - `RETENTION_KEEP_WEEKLY` (дефолт 12)
  - `RETENTION_KEEP_MONTHLY` (дефолт 60 ≈ 5 лет)
- restore-check (опционально, по умолчанию включён): `ENABLE_RESTORE_CHECK=1`, `RESTORE_CHECK_CRON` (вс 03:00)

### Частые “версии” БД (backup_orders)
**Причина отдельного подхода**: restic **не умеет** смешивать `--stdin` и обычные пути (media) в одном снапшоте.

Поэтому `backup_orders` хранит **DB-only**:
- использует атомарный SQLite `.backup` → затем `restic backup --stdin --stdin-filename data/db.sqlite3`
- retention: `RETENTION_KEEP_LAST_ORDERS` (дефолт 2000)
- `prune` ограничен: `PRUNE_INTERVAL_MIN_ORDERS` (дефолт 60 минут)
- скрипт переопределён bind-mount’ом:
  - host: `docker/backup/run_backup_sqlite_orders.sh`
  - container: `/backup/run_backup_sqlite.sh`

### Полезные команды (внутри Docker)
- список снапшотов:
  - `docker compose exec -T backup restic snapshots --compact`
- восстановление снапшота в папку на хосте:
  - `docker compose exec -T backup restic restore <SNAPSHOT_ID> --target /restic/restore --include "/data/db.sqlite3" --include "/data/media"`
  - затем на хосте заменить `db.sqlite3` и `media/` (остановив сервисы).

## Текущее состояние тестов/QA
- Папка `website/tests/` **пустая** (автотестов сейчас нет).
- В `website/management/commands/` есть генераторы данных (`create_test_records.py`, `create_products.py` и т.д.), но отдельной “QA seed” команды нет.

## Частые ошибки/нюансы
- `/profiles/` требует логин → редиректит на `/accounts/login/` (которого нет) и получается 404.
  - Правильный логин: через `/` (главная).
- При правках в compose/env для cron:
  - не добавлять лишние кавычки в значения переменных, иначе cron/retention ломаются.
- При удалении `db.sqlite3`:
  - удалять/пересоздавать корректно, иначе Docker создаст папку и Django не поднимется.


