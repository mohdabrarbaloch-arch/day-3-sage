# Sage — Architecture

Sage is a Claude-style long-context reasoning assistant. You upload long documents (text, Markdown, or PDF), ask questions, and get answers that are **grounded in the exact sentences they came from** — with citations. It can also compress a long document into an extractive summary.

## System diagram (text)

```
┌────────────────────┐
│  Browser (SPA)      │  vanilla JS, no build step
│  index.html/styles  │
└─────────┬──────────┘
          │  JSON over HTTP  (JWT Bearer)
          ▼
┌────────────────────────────────────┐
│  FastAPI (app/main.py)              │
│  ├─ /api/auth          signup/login │
│  ├─ /api/documents     upload/list  │
│  ├─ /api/conversations ask/history  │
│  ├─ /api/summarize     extractive   │
│  └─ /api/health        probe        │
└──────┬──────────────────┬──────────┘
       │                  │
       ▼                  ▼
┌───────────────┐   ┌──────────────────────────────┐
│  SQLAlchemy   │   │  services/                    │
│  (SQLite / PG) │   │  extraction, chunking,        │
└───────────────┘   │  retrieval, summarizer,        │
                    │  guardrails                    │
                    └──────────────────────────────┘
```

## Tech stack

- **Backend:** Python 3.11, FastAPI 0.115, Uvicorn, Pydantic v2
- **Database:** SQLAlchemy 2.0 ORM — SQLite in dev, PostgreSQL 16 in production via docker-compose
- **Auth:** JWT (HS256, PyJWT) + bcrypt (passlib)
- **Documents:** PyPDF2 for PDF text extraction
- **Rate limiting:** slowapi
- **Frontend:** vanilla HTML/CSS/JS, mobile-first, zero build step
- **Deploy:** Vercel serverless (`api/index.py` + `vercel.json`) or Docker

## Data flow (ask a question)

1. Browser POSTs `{question, document_id}` to `/api/conversations/ask` with a Bearer token.
2. `get_current_user` decodes the JWT and loads the user.
3. The question passes through `guardrails.flag_question` — harmful prompts are refused and the refusal is persisted.
4. `retrieval.answer` chunks the document, scores chunks by TF-IDF lexical overlap, extracts the best-matching sentences.
5. If no chunk clears the threshold, Sage returns an honest refusal (`grounded: false`).
6. The exchange is stored as two `Message` rows and returned with `citations`.

## The grounding guarantee

Sage's answer engine is **extractive, not generative**. It selects sentences from the source document and stitches them together. It cannot paraphrase, so it cannot hallucinate. This is the core safety property: when nothing clears the relevance threshold, it says so rather than guessing.

## Scaling notes

- **SQLite → PostgreSQL:** flip `DATABASE_URL`; the ORM layer is unchanged.
- **Chunking:** the chunker is O(n) over sentences and cheap; for very large corpora move to a vector index (pgvector / Qdrant) with the same citation contract.
- **Extractive → generative:** an optional LLM provider can be layered behind the same `grounded`/`citations` response shape without touching the API contract.
- **Rate limiting:** per-route limits via slowapi; swap for a Redis-backed limiter when scaling horizontally.
- **Stateless serverless:** all state is in the database; a serverless function can serve any request without a warm process.
