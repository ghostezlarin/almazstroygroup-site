from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

STATUSES = {
    "new": "Новая",
    "in_work": "В работе",
    "done": "Закрыта",
    "spam": "Спам",
}


class Lead(db.Model):
    """Заявка клиента: ремонт, дизайн-проект, конкретная услуга, смета."""

    __tablename__ = "leads"

    KINDS = {
        "repair": "Ремонтные работы",
        "design": "Дизайн-проект",
        "estimate": "Бесплатная смета",
        "consult": "Консультация",
    }

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False, default="consult")
    service = db.Column(db.String(120))  # конкретная услуга со страницы «Услуги»
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    object_type = db.Column(db.String(60))  # квартира / дом / коммерция
    area = db.Column(db.String(20))  # м²
    comment = db.Column(db.Text)
    source = db.Column(db.String(120))  # страница / кнопка, откуда пришла заявка
    status = db.Column(db.String(20), nullable=False, default="new")
    tg_sent = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    @property
    def kind_label(self):
        return self.KINDS.get(self.kind, self.kind)


class Partnership(db.Model):
    """Заявка на сотрудничество: вакансия, подрядчик, поставщик."""

    __tablename__ = "partnerships"

    TYPES = {
        "staff": "Работа в штате",
        "contractor": "Подрядчик / бригада",
        "supplier": "Поставщик / производитель",
        "designer": "Дизайнер / архитектор",
    }

    id = db.Column(db.Integer, primary_key=True)
    coop_type = db.Column(db.String(20), nullable=False, default="staff")
    name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(160))
    company = db.Column(db.String(160))
    specialization = db.Column(db.String(160))
    experience = db.Column(db.String(40))
    city = db.Column(db.String(120))
    portfolio = db.Column(db.String(300))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="new")
    tg_sent = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    @property
    def type_label(self):
        return self.TYPES.get(self.coop_type, self.coop_type)
