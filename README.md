<div align="center">

# Handin

**A simple hand-in page builder, made for Utrecht University.**

[![CI](https://img.shields.io/github/actions/workflow/status/JustinZeus/handin-website/ci.yml?style=for-the-badge)](https://github.com/JustinZeus/handin-website/actions/workflows/ci.yml)
[![Docker Pulls](https://img.shields.io/docker/pulls/justinzeus/handin?style=for-the-badge&logo=docker)](https://hub.docker.com/r/justinzeus/handin)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

</div>

---

## What is this?

I built this as a boilerplate for group hand-ins at Utrecht University. It lets you combine PDFs, video, audio, markdown, embedded content, image galleries, and team member listings into a multi-page website. I'm making it publicly available in case anyone else finds it useful.

## Features

- **Multimodal content** — markdown, PDF, video, audio, iframes, image galleries, and team members
- **Multi-page** — create and manage multiple pages, each with its own slug and segments
- **Drag-and-drop ordering** — reorder pages and segments visually
- **Token-based admin** — single admin token, no user accounts needed
- **Dark mode** — automatic dark/light theme
- **Zero-config database** — SQLite with WAL mode, no external DB to manage
- **Single container** — FastAPI backend + Vue 3 SPA ship as one Docker image

## Deployment

Create a `compose.yml`:

```yaml
name: handin

services:
  handin:
    image: justinzeus/handin:latest
    restart: unless-stopped
    environment:
      HANDIN_ADMIN_TOKEN: ${HANDIN_ADMIN_TOKEN:?set HANDIN_ADMIN_TOKEN}
      HANDIN_SITE_TITLE: ${HANDIN_SITE_TITLE:-Untitled Site}
      HANDIN_DATA_DIR: /data
    volumes:
      - handin_data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 10s
      timeout: 5s
      retries: 12

volumes:
  handin_data:
```

Then:

```bash
export HANDIN_ADMIN_TOKEN=$(openssl rand -hex 32)
docker compose up -d
```

The app listens on port 8000. Wire it through your reverse proxy (e.g. Caddy) to expose it.

## How It Works

```mermaid
graph LR
    Browser <-->|HTTP| FastAPI[FastAPI + Vue SPA]
    FastAPI --> DB[(SQLite)]
    FastAPI --> Assets[/data/assets/]
```

The Vue 3 frontend is built at image build time and served as static files by FastAPI. All data (database + uploaded assets) lives in a single `/data` volume.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HANDIN_ADMIN_TOKEN` | *required* | Bearer token for admin endpoints |
| `HANDIN_SITE_TITLE` | `Untitled Site` | Page title shown in the browser tab |
| `HANDIN_DATA_DIR` | `./data` | SQLite DB + uploaded assets directory |
| `HANDIN_MAX_UPLOAD_BYTES` | `100000000` | Max file upload size (~100 MB) |
| `HANDIN_ALLOWED_UPLOAD_TYPES` | `pdf,png,jpg,...` | Comma-separated allowed file extensions |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLite |
| Frontend | TypeScript, Vue 3, Vite, Tailwind CSS v4 |
| Infrastructure | Multi-stage Docker, Docker Compose, UV |

## Development

```bash
# Start backend + frontend dev server
docker compose up

# Or run locally:

# Backend
uv sync --group dev
uv run fastapi dev backend/app/main.py --port 8000

# Frontend (separate terminal)
cd frontend
npm ci
npm run dev
```

Lint and type-check:

```bash
# Backend
uv run ruff check backend/
uv run ruff format --check backend/
uv run mypy
uv run pytest

# Frontend
cd frontend
npx vue-tsc --noEmit
```
