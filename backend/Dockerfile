# ─── Stage 1: Builder ────────────────────────────────────────────
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# ─── Stage 2: Development ─────────────────────────────────────────
FROM python:3.11-slim as development

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ─── Stage 3: Production ──────────────────────────────────────────
FROM python:3.11-slim as production

RUN addgroup --system app && adduser --system --group app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

COPY --chown=app:app . .
RUN chmod +x entrypoint.sh

USER app
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
