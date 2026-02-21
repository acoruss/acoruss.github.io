# ============================================================
# Stage 1: Build frontend assets (Tailwind CSS + DaisyUI)
# ============================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --include=dev 2>/dev/null || npm install --include=dev

COPY frontend/ ./
COPY src/templates/ /app/src/templates/
COPY src/static/js/ /app/src/static/js/

RUN npm run minify

# ============================================================
# Stage 2: Python base
# ============================================================
FROM python:3.13-slim AS python-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./

# ============================================================
# Stage 3: Development
# ============================================================
FROM python-base AS development

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

ENV DJANGO_SETTINGS_MODULE=config.settings.dev

COPY . .

# Copy images to static
RUN mkdir -p src/static/images/logos \
    && cp -r public/images/logos/* src/static/images/logos/ 2>/dev/null || true

EXPOSE 8000

CMD ["sh", "-c", "cd /app/src && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

# ============================================================
# Stage 4: Production
# ============================================================
FROM python-base AS production

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

ENV DJANGO_SETTINGS_MODULE=config.settings.prod

# Create non-root user
RUN groupadd -r acoruss && useradd -r -g acoruss -d /app -s /sbin/nologin acoruss

# Copy application code
COPY src/ ./src/
COPY public/ ./public/

# Copy built frontend assets
COPY --from=frontend-builder /app/src/static/css/main.css ./src/static/css/main.css

# Copy images to static
RUN mkdir -p src/static/images/logos \
    && cp -r public/images/logos/* src/static/images/logos/

# Collect static files
RUN cd src && python manage.py collectstatic --noinput 2>/dev/null || true

RUN chown -R acoruss:acoruss /app

USER acoruss

EXPOSE 8000

CMD ["gunicorn", "config.asgi:application", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--chdir", "/app/src", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]