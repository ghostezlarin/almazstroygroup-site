import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


DEV_SECRET_KEY = "dev-secret-change-me"
DEV_ADMIN_PASSWORD = "admin"


class Config:
    # APP_ENV=production и TRUST_PROXY=1 задаёт docker-compose.yml
    PRODUCTION = os.getenv("APP_ENV") == "production"
    TRUST_PROXY = os.getenv("TRUST_PROXY") == "1"

    SECRET_KEY = os.getenv("SECRET_KEY") or DEV_SECRET_KEY

    # SQLite по умолчанию; для продакшена можно указать PostgreSQL/MySQL:
    # DATABASE_URL=postgresql+psycopg://user:pass@host/db
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'site.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    # Один или несколько chat_id через запятую (личка, группа, канал)
    TELEGRAM_CHAT_IDS = [c.strip() for c in os.getenv("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]

    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or DEV_ADMIN_PASSWORD
    SITE_URL = os.getenv("SITE_URL", "").rstrip("/")

    # Cookie сессии только по HTTPS, как только сайт работает на https-адресе
    SESSION_COOKIE_SECURE = SITE_URL.startswith("https://")
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 1024 * 1024  # формы текстовые, файлов сайт не принимает
