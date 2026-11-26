"""Отправка заявок в Telegram-бота через Bot API (без сторонних библиотек ботов)."""

import logging
import threading
from html import escape

import requests

log = logging.getLogger(__name__)
API = "https://api.telegram.org/bot{token}/{method}"


def _row(label, value):
    if not value:
        return ""
    return f"<b>{label}:</b> {escape(str(value))}\n"


def _phone_link(phone):
    # tel:-ссылки Telegram не принимает, но номер в формате +7… он сам делает кликабельным
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 11 and digits[0] in "78":
        digits = "7" + digits[1:]
    return f"<b>Телефон:</b> +{digits}\n" if digits else _row("Телефон", phone)


def format_lead(lead, admin_url=""):
    icon = {"repair": "🛠", "design": "📐", "estimate": "🧾"}.get(lead.kind, "💬")
    text = f"{icon} <b>Новая заявка №{lead.id} — {escape(lead.kind_label)}</b>\n\n"
    text += _row("Услуга", lead.service)
    text += _row("Имя", lead.name)
    text += _phone_link(lead.phone)
    text += _row("Объект", lead.object_type)
    text += _row("Площадь", f"{lead.area} м²" if lead.area else "")
    text += _row("Комментарий", lead.comment)
    text += f"\n<i>{escape(lead.source or 'сайт')} · {lead.created_at:%d.%m.%Y %H:%M}</i>"
    if admin_url:
        text += f'\n<a href="{escape(admin_url)}">Открыть в панели заявок</a>'
    return text


def format_partnership(p, admin_url=""):
    text = f"🤝 <b>Заявка на сотрудничество №{p.id} — {escape(p.type_label)}</b>\n\n"
    text += _row("Имя", p.name)
    text += _phone_link(p.phone)
    text += _row("Email", p.email)
    text += _row("Компания", p.company)
    text += _row("Специализация", p.specialization)
    text += _row("Опыт", p.experience)
    text += _row("Город", p.city)
    text += _row("Портфолио", p.portfolio)
    text += _row("О себе", p.message)
    text += f"\n<i>{p.created_at:%d.%m.%Y %H:%M}</i>"
    if admin_url:
        text += f'\n<a href="{escape(admin_url)}">Открыть в панели заявок</a>'
    return text


def send_message(token, chat_ids, text):
    """Возвращает True, если сообщение ушло хотя бы в один чат."""
    if not token or not chat_ids:
        log.warning("Telegram не настроен (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) — уведомление пропущено")
        return False
    ok = False
    for chat_id in chat_ids:
        try:
            r = requests.post(
                API.format(token=token, method="sendMessage"),
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=10,
            )
            if r.ok:
                ok = True
            else:
                log.error("Telegram %s: %s", chat_id, r.text)
        except requests.RequestException as e:
            log.error("Telegram %s: %s", chat_id, e)
    return ok


def notify_async(app, model, obj_id, formatter, admin_path):
    """Отправляет уведомление в фоне, чтобы форма отвечала мгновенно, и помечает tg_sent."""

    def worker():
        with app.app_context():
            from models import db

            obj = db.session.get(model, obj_id)
            if obj is None:
                return
            base = app.config["SITE_URL"]
            text = formatter(obj, f"{base}{admin_path}" if base else "")
            if send_message(app.config["TELEGRAM_BOT_TOKEN"], app.config["TELEGRAM_CHAT_IDS"], text):
                obj.tg_sent = True
                db.session.commit()

    threading.Thread(target=worker, daemon=True).start()
