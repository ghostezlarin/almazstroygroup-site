"""Помогает узнать chat_id: напишите боту /start (или добавьте его в группу) и запустите скрипт."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    raise SystemExit("Сначала укажите TELEGRAM_BOT_TOKEN в .env")

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10).json()
if not r.get("ok"):
    raise SystemExit(f"Ошибка Telegram: {r}")

seen = {}
for upd in r["result"]:
    msg = upd.get("message") or upd.get("channel_post") or upd.get("my_chat_member") or {}
    chat = msg.get("chat")
    if chat:
        seen[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("first_name")

if not seen:
    print("Сообщений нет. Напишите боту /start и запустите скрипт ещё раз.")
for chat_id, name in seen.items():
    print(f"{chat_id}\t{name}")
