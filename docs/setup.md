# Setup

## Prerequisites

- Python 3.11+
- (optional) Docker for the Postgres stack

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The SPA loads at http://localhost:8000.

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./sage.db` | Database URL (use Postgres in prod) |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key — set a strong value |
| `MAX_UPLOAD_BYTES` | `20971520` | Upload size cap (20 MB) |
| `ALLOWED_EXTENSIONS` | `.txt,.md,.pdf` | Upload allow-list |
| `RATE_LIMIT` | `100/minute` | Default rate limit |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |

## Docker

```bash
docker compose up --build
```

This boots a Postgres 16 container plus the API on http://localhost:8000.
