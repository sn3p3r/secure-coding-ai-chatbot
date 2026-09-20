FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_DEBUG=0 \
    PORT=8000 \
    ACADEMY_DB=/data/academy.db \
    ACADEMY_AVATARS_DIR=/data/avatars

# Mount a volume at /data so accounts and progress survive restarts.
VOLUME ["/data"]
EXPOSE 8000

CMD ["sh", "-c", "gunicorn --preload --workers 2 --bind 0.0.0.0:${PORT} app:app"]
