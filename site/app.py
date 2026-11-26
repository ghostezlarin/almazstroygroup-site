import logging
import re
import secrets
import time
from collections import defaultdict, deque
from functools import wraps
from pathlib import Path

from flask import (Flask, abort, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from markupsafe import Markup
from sqlalchemy import func, text
from werkzeug.middleware.proxy_fix import ProxyFix

import content
from config import BASE_DIR, DEV_ADMIN_PASSWORD, DEV_SECRET_KEY, Config
from models import STATUSES, Lead, Partnership, db
from telegram_notify import format_lead, format_partnership, notify_async, send_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = Flask(__name__, instance_path=str(BASE_DIR / "instance"))
app.config.from_object(Config)

if app.config["PRODUCTION"]:
    # На сервере лучше не запуститься, чем открыть панель заявок со стандартным паролем
    if app.config["SECRET_KEY"] == DEV_SECRET_KEY or len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("Задайте в .env случайный SECRET_KEY длиной от 32 символов")
    if app.config["ADMIN_PASSWORD"] == DEV_ADMIN_PASSWORD or len(app.config["ADMIN_PASSWORD"]) < 10:
        raise RuntimeError("Задайте в .env ADMIN_PASSWORD длиной от 10 символов")

if app.config["TRUST_PROXY"]:
    # Реальный IP и https берём из заголовков единственного прокси — Caddy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

Path(app.instance_path).mkdir(exist_ok=True)
db.init_app(app)

with app.app_context():
    db.create_all()


# ---------- helpers ----------

ICON_DIR = BASE_DIR / "static" / "img" / "social"
_icons = {}


def icon(name):
    """Инлайн-SVG иконки соцсети, окрашивается через currentColor."""
    if name not in _icons:
        svg = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
        svg = re.sub(r"<title>.*?</title>", "", svg)
        _icons[name] = svg.replace("<svg ", '<svg fill="currentColor" aria-hidden="true" ', 1)
    return Markup(_icons[name])


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def csrf_ok(value):
    expected = session.get("csrf")
    return bool(expected and value) and secrets.compare_digest(value.encode(), expected.encode())


@app.context_processor
def inject_globals():
    return {"C": content, "icon": icon, "csrf_token": csrf_token, "STATUSES": STATUSES,
            "Lead": Lead, "Partnership": Partnership}


_hits = defaultdict(deque)


def rate_limited(limit=5, window=600, scope="forms"):
    q, now = _hits[(scope, request.remote_addr)], time.time()
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def clean(value, maxlen):
    return (value or "").strip()[:maxlen]


def validate_contact(data, errors):
    name = clean(data.get("name"), 120)
    phone = clean(data.get("phone"), 40)
    if len(name) < 2:
        errors["name"] = "Укажите имя"
    if len(re.sub(r"\D", "", phone)) < 10:
        errors["phone"] = "Укажите телефон полностью"
    if str(data.get("consent", "")).lower() not in ("1", "true", "on", "yes"):
        errors["consent"] = "Нужно согласие на обработку данных"
    return name, phone


def guard_form(data):
    """Общие проверки для публичных форм. Возвращает ответ-ошибку или None."""
    if not csrf_ok(request.headers.get("X-CSRF-Token")):
        return jsonify(ok=False, message="Сессия устарела, обновите страницу"), 400
    if data.get("website"):  # honeypot — поле скрыто от людей
        return jsonify(ok=True), 200
    if rate_limited():
        return jsonify(ok=False, message="Слишком много заявок, попробуйте позже"), 429
    return None


# ---------- public pages ----------

@app.route("/healthz")
def healthz():
    db.session.execute(text("SELECT 1"))
    return "ok"


@app.route("/")
def index():
    return render_template("index.html", page="home")


@app.route("/services")
def services():
    return render_template("services.html", page="services")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html", page="gallery")


@app.route("/about")
def about():
    return render_template("about.html", page="about")


@app.route("/contacts")
def contacts():
    return render_template("contacts.html", page="contacts")


@app.route("/team")
def team():
    return render_template("team.html", page="team")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html", page="privacy")


# ---------- forms API ----------

@app.post("/api/lead")
def api_lead():
    data = request.get_json(silent=True) or request.form
    if (resp := guard_form(data)) is not None:
        return resp
    errors = {}
    name, phone = validate_contact(data, errors)
    if errors:
        return jsonify(ok=False, errors=errors), 422

    kind = data.get("kind") if data.get("kind") in Lead.KINDS else "consult"
    lead = Lead(
        kind=kind,
        service=clean(data.get("service"), 120) or None,
        name=name,
        phone=phone,
        object_type=clean(data.get("object_type"), 60) or None,
        area=clean(data.get("area"), 20) or None,
        comment=clean(data.get("comment"), 2000) or None,
        source=clean(data.get("source"), 120) or None,
    )
    db.session.add(lead)
    db.session.commit()
    notify_async(app, Lead, lead.id, format_lead, url_for("admin_leads") + f"#lead-{lead.id}")
    return jsonify(ok=True, id=lead.id)


@app.post("/api/partnership")
def api_partnership():
    data = request.get_json(silent=True) or request.form
    if (resp := guard_form(data)) is not None:
        return resp
    errors = {}
    name, phone = validate_contact(data, errors)
    email = clean(data.get("email"), 160)
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors["email"] = "Проверьте email"
    if errors:
        return jsonify(ok=False, errors=errors), 422

    coop_type = data.get("coop_type") if data.get("coop_type") in Partnership.TYPES else "staff"
    p = Partnership(
        coop_type=coop_type,
        name=name,
        phone=phone,
        email=email or None,
        company=clean(data.get("company"), 160) or None,
        specialization=clean(data.get("specialization"), 160) or None,
        experience=clean(data.get("experience"), 40) or None,
        city=clean(data.get("city"), 120) or None,
        portfolio=clean(data.get("portfolio"), 300) or None,
        message=clean(data.get("message"), 3000) or None,
    )
    db.session.add(p)
    db.session.commit()
    notify_async(app, Partnership, p.id, format_partnership, url_for("admin_partners") + f"#partner-{p.id}")
    return jsonify(ok=True, id=p.id)


# ---------- admin ----------

def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if not csrf_ok(request.form.get("csrf")):
            abort(400)
        if rate_limited(limit=10, scope="login"):
            flash("Слишком много попыток входа, попробуйте через 10 минут")
            return render_template("admin/login.html"), 429
        password = request.form.get("password", "").encode()
        if secrets.compare_digest(password, app.config["ADMIN_PASSWORD"].encode()):
            session["admin"] = True
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/admin") else url_for("admin_leads"))
        flash("Неверный пароль")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


MODELS = {"leads": Lead, "partners": Partnership}


def admin_counts():
    out = {}
    for key, model in MODELS.items():
        out[key] = {
            "all": db.session.scalar(db.select(func.count()).select_from(model)),
            "new": db.session.scalar(db.select(func.count()).select_from(model).where(model.status == "new")),
        }
    return out


def admin_list(key):
    model = MODELS[key]
    status = request.args.get("status", "")
    q = clean(request.args.get("q"), 100)
    stmt = db.select(model).order_by(model.created_at.desc())
    if status in STATUSES:
        stmt = stmt.where(model.status == status)
    else:
        stmt = stmt.where(model.status != "spam")
    if key == "leads" and request.args.get("kind") in Lead.KINDS:
        stmt = stmt.where(Lead.kind == request.args["kind"])
    if key == "partners" and request.args.get("type") in Partnership.TYPES:
        stmt = stmt.where(Partnership.coop_type == request.args["type"])
    if q:
        like = f"%{q}%"
        stmt = stmt.where(model.name.ilike(like) | model.phone.ilike(like))
    items = db.session.scalars(stmt.limit(500)).all()
    return render_template("admin/list.html", tab=key, items=items, counts=admin_counts(),
                           status=status, q=q, args=request.args)


@app.route("/admin")
@admin_required
def admin_index():
    return redirect(url_for("admin_leads"))


@app.route("/admin/leads")
@admin_required
def admin_leads():
    return admin_list("leads")


@app.route("/admin/partners")
@admin_required
def admin_partners():
    return admin_list("partners")


@app.post("/admin/<key>/<int:obj_id>/status")
@admin_required
def admin_set_status(key, obj_id):
    if key not in MODELS or not csrf_ok(request.form.get("csrf")):
        abort(400)
    obj = db.get_or_404(MODELS[key], obj_id)
    if request.form.get("status") in STATUSES:
        obj.status = request.form["status"]
        db.session.commit()
    return redirect(request.referrer or url_for("admin_index"))


@app.post("/admin/<key>/<int:obj_id>/resend")
@admin_required
def admin_resend(key, obj_id):
    if key not in MODELS or not csrf_ok(request.form.get("csrf")):
        abort(400)
    obj = db.get_or_404(MODELS[key], obj_id)
    fmt = format_lead if key == "leads" else format_partnership
    if send_message(app.config["TELEGRAM_BOT_TOKEN"], app.config["TELEGRAM_CHAT_IDS"], fmt(obj)):
        obj.tg_sent = True
        db.session.commit()
        flash(f"Заявка №{obj.id} отправлена в Telegram")
    else:
        flash("Не удалось отправить в Telegram — проверьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env")
    return redirect(request.referrer or url_for("admin_index"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", page="404"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
