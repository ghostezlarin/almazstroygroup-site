FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Приложение работает не от root; база лежит в томе, смонтированном в instance/
RUN useradd --create-home --uid 1000 app \
    && mkdir -p instance \
    && chown -R app:app instance
USER app

EXPOSE 8000

# Один процесс с потоками: SQLite и счётчик лимитов заявок живут в одном процессе
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--access-logfile", "-"]
