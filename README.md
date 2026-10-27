# Sage

A Claude-style long-context reasoning assistant. Upload long documents, ask questions, and get **grounded answers with citations** — plus extractive summaries. The answer engine quotes your files and refuses when it can't find an answer, so it never hallucinates.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## What it does

- **Upload** `.txt`, `.md`, and `.pdf` files (PDF text extracted with PyPDF2)
- **Ask questions** and get answers with citations to the exact sentences used
- **Grounded or honest:** when nothing matches, Sage says so instead of inventing an answer
- **Summarize** long documents with an extractive, position-aware algorithm
- **Auth** with JWT + bcrypt, per-user documents and conversation history
- **Guardrails** that refuse clearly harmful prompts (and persist the refusal)
- **Rate limiting** on sensitive routes

## Why it doesn't hallucinate

Sage's default answer engine is extractive: it scores your document's sentences and returns the best ones verbatim. It cannot paraphrase, so it cannot fabricate. The `grounded` flag travels with every answer, and the UI labels ungrounded refusals distinctly.

## Live demo

> Not yet deployed — see **Deployment** below. The production build is verified locally.

## Screenshots

*Coming soon — a deployed instance is needed to capture them. See **Deployment**.*

## Install & run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000 — the SPA is served at `/`.

### With Docker

```bash
docker compose up --build
```

## Environment

Copy `.env.example` to `.env` and set `SECRET_KEY` (and `DATABASE_URL` for Postgres).

## Tests

```bash
pytest
ruff check .
black --check .
```

## Deployment

Deploy-ready on Vercel (`vercel.json` + `api/index.py` + `includeFiles` bundles the full `app/` package). Blocked only by the missing `VERCEL_TOKEN` in the build environment.

## License

MIT — see `LICENSE`.
