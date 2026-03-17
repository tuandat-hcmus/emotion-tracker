# Emotion Tracker

This repository is now split so backend and frontend work can happen in parallel. The current product direction is English-first:

- main product language: English
- primary backend demo path: English AI core
- Vietnamese is kept as a secondary localization/demo path
- Chinese and audio are not active product priorities right now

- `backend/`: FastAPI backend, tests, Alembic migrations, scripts, and backend docs
- `frontend/`: reserved for frontend app code

## Backend

Run backend commands from the `backend/` folder.

Example:

```bash
cd backend
python -m pytest
uvicorn app.main:app --reload
```

English-first demo:

```bash
cd backend
cp .env.demo.en.example .env
python -m uvicorn app.main:app --reload
```

Then hit:

```text
POST /v1/demo/ai-core
```

For detailed backend setup, supported models, Gemini rendering, and the Vietnamese localization path, see [backend/README.md](backend/README.md).

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
