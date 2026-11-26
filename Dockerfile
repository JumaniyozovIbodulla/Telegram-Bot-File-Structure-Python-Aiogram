# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create a non-root user for security
RUN addgroup --system botuser && adduser --system --ingroup botuser botuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy only runtime application code
COPY --chown=botuser:botuser main.py ./
COPY --chown=botuser:botuser data ./data
COPY --chown=botuser:botuser filters ./filters
COPY --chown=botuser:botuser handlers ./handlers
COPY --chown=botuser:botuser keyboards ./keyboards
COPY --chown=botuser:botuser middlewares ./middlewares
COPY --chown=botuser:botuser services ./services
COPY --chown=botuser:botuser states ./states
COPY --chown=botuser:botuser utils ./utils

# Persistent directory for SQLite database (safe from overwriting /app/data/*.py)
RUN mkdir -p /app/storage && chown -R botuser:botuser /app/storage

USER botuser

CMD ["python", "main.py"]
