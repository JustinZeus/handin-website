# ---- Stage 1: Build frontend ----
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---- Stage 2: Dev (includes dev dependencies) ----
FROM python:3.12-slim AS dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --group dev

COPY backend/ backend/
COPY scripts/ scripts/

ENTRYPOINT ["/bin/sh", "/app/scripts/entrypoint.sh"]

# ---- Stage 3: Production (minimal, no dev deps) ----
FROM python:3.12-slim AS prod

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ backend/
COPY --from=frontend-builder /build/dist static/
COPY scripts/ scripts/

EXPOSE 8000
ENTRYPOINT ["/bin/sh", "/app/scripts/entrypoint.sh"]
