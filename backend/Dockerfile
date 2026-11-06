FROM python:3.12-slim

# Production-safe defaults. The env guard in app/main.py refuses to start
# unless SECRET_KEY and FIRST_ADMIN_PASSWORD are overridden with real values
# (docker run -e / compose env_file / secret manager). Local `docker compose`
# reads backend/.env, which sets ENVIRONMENT=dev again for development.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=prod \
    AUTO_CREATE_TABLES=false \
    FIRST_ADMIN_RESET_ON_STARTUP=false

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8035

# Schema is owned by Alembic; migrate before serving.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8035"]
