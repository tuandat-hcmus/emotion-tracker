# Emotion Tracker

This repository contains a FastAPI backend and a lightweight frontend shell for an emotional wellness journaling product.

Current product and backend guidelines:
- English is the default response language unless a supported user language override is clear.
- The canonical frontend emotion contract uses 7 labels only:
  - `anger`
  - `disgust`
  - `fear`
  - `joy`
  - `sadness`
  - `surprise`
  - `neutral`
- The local Hugging Face emotion model is the only source of truth for emotion detection.
- Deterministic backend services handle:
  - state normalization
  - safety
  - response planning
  - response policy
- Gemini is renderer-only. It does not classify emotion and must not invent unsupported facts.
- Check-ins support both:
  - text input
  - voice input via `upload -> STT -> shared normalized transcript pipeline`

Repository layout:
- `backend/`: FastAPI backend, tests, Alembic migrations, scripts, and backend docs
- `frontend/`: frontend app or static dashboard shell

## Backend

Run backend commands from the `backend/` folder.

Important backend behavior:
- text check-ins are persisted and processed end-to-end
- voice check-ins reuse the same downstream transcript pipeline
- check-in lifecycle is hardened against duplicate processing calls and partial-write failures
- history endpoints expose lightweight canonical timeline data
- wrapups and summaries are generated from persisted journal entries and stored AI snapshots

Docker Compose local dev:

```bash
docker compose up --build
```

Windows launcher:

```bat
run-dev.bat
```

Useful Docker commands:

```bash
docker compose exec app alembic upgrade head
docker compose exec db psql -U emotion_user -d emotion_app
docker compose down
docker compose down -v
```

Example:

```bash
cd backend
cp .env.example .env
alembic upgrade head
python -m pytest
uvicorn app.main:app --reload
```

Main authenticated product flows:

```text
POST /v1/checkins/text
POST /v1/checkins/upload
POST /v1/checkins/{entry_id}/process
GET  /v1/checkins/{entry_id}
GET  /v1/users/{user_id}/entries
GET  /v1/users/{user_id}/summary
GET  /v1/me/wrapups/weekly/latest
GET  /v1/me/wrapups/monthly/latest
POST /v1/me/wrapups/regenerate
```

English-first demo flow:

```bash
cd backend
cp .env.demo.en.example .env
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Then hit:

```text
POST /v1/demo/ai-core
```

For detailed backend setup, architecture, contracts, and operational notes, see [backend/README.md](backend/README.md).

## Frontend

`frontend/` now contains a dependency-free static dashboard shell for the existing backend APIs.

Run it with a local static server from the repo root:

```bash
cd frontend
../.venv/bin/python -m http.server 5173
```

Then open:

```text
http://127.0.0.1:5173
```

The UI expects the backend to be running, defaulting to `http://127.0.0.1:8000`.
