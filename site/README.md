# Алмазстройгрупп — сайт (Flask + SQL)

## Запуск

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # и заполнить
python app.py
```

Сайт: http://127.0.0.1:5000 · Панель заявок: http://127.0.0.1:5000/admin (пароль — `ADMIN_PASSWORD` из `.env`).

## Telegram-бот

1. В Telegram откройте @BotFather → `/newbot` → скопируйте токен в `TELEGRAM_BOT_TOKEN`.
2. Напишите своему боту `/start` (или добавьте бота в рабочую группу).
3. `python get_chat_id.py` — выведет `chat_id`, впишите его в `TELEGRAM_CHAT_ID` (можно несколько через запятую).
4. Перезапустите сайт. Каждая заявка сохраняется в БД и уходит в Telegram; если отправка не удалась, в панели появится кнопка «↻ В Telegram».

## Запуск в Docker (на сервере)

Нужны Docker и Docker Compose, открытые порты 80 и 443.

```bash
cp .env.example .env            # заполнить: SECRET_KEY, ADMIN_PASSWORD, Telegram, SITE_URL
docker compose up -d --build
docker compose ps
```

- `web` — приложение (gunicorn), наружу не открыто; `caddy` — принимает запросы на 80/443.
- С доменом: укажите в `.env` `SITE_ADDRESS=example.ru` и `SITE_URL=https://example.ru` — сертификат HTTPS Caddy получит сам. DNS домена должен указывать на сервер.
- Заявки хранятся в томе `site-data` и переживают пересборку контейнеров.
- Логи: `docker compose logs -f web`. Обновление: залить новые файлы и повторить `docker compose up -d --build`.
- Резервная копия базы:

```bash
docker compose exec web python -c "import sqlite3; s = sqlite3.connect('instance/site.db'); d = sqlite3.connect('instance/backup.db'); s.backup(d)"
docker compose cp web:/app/instance/backup.db ./backup.db
```

## Структура

| Файл | Что внутри |
|---|---|
| `app.py` | маршруты страниц, API форм (`/api/lead`, `/api/partnership`), панель `/admin` |
| `models.py` | таблицы `leads` (клиенты) и `partnerships` (сотрудничество) |
| `telegram_notify.py` | форматирование и отправка сообщений в бота |
| `content.py` | тексты, услуги, проекты галереи, этапы, точки карты |
| `templates/` | страницы: главная, услуги, галерея, о нас, контакты, сотрудничество |
| `static/` | стили, скрипты, изображения из макетов |
