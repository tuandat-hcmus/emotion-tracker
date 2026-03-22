# Emotion Tracker

This repository contains the current Emotion product:
- `backend/`: FastAPI API, database models, Alembic migrations, tests, and AI/service logic
- `frontend/webapp/`: React Router + TypeScript frontend

The product is an emotional wellness journaling app with:
- text check-ins
- realtime conversation sessions
- history and summaries
- backend-owned emotion analysis and response logic

## Product Rules

- The local Hugging Face model is the source of truth for emotion inference.
- Gemini is renderer-only.
- The canonical emotion labels are:
  - `anger`
  - `disgust`
  - `fear`
  - `joy`
  - `sadness`
  - `surprise`
  - `neutral`
- Business logic stays on the backend.
- The frontend should only render backend-backed fields and remain resilient to additive fields.

## Repository Layout

```text
Emotion/
├─ backend/
├─ frontend/
│  └─ webapp/
├─ docker-compose.yml
└─ run-dev.bat
```

## Local Run Guide

You need 2 terminals:
- one for the backend
- one for the frontend

### 1. Backend setup

From the repo root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ai.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-ai.txt
Copy-Item .env.example .env
```

Important:
- update `backend/.env` if your local database URL is different
- add both frontend origins to `BACKEND_CORS_ORIGINS`

Recommended value:

```env
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```

Run migrations:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Windows PowerShell:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Start the backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Backend default URL:

```text
http://127.0.0.1:8000
```

### 2. Frontend setup

The real frontend app is in `frontend/webapp`, not `frontend`.

From the repo root:

```bash
cd frontend/webapp
npm install
cp .env.example .env
```

Windows PowerShell:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\frontend\webapp
npm install
Copy-Item .env.example .env
```

Frontend env:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
cd frontend/webapp
npm run dev
```

Windows PowerShell:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\frontend\webapp
npm run dev
```

Frontend default URL:

```text
http://localhost:5173
```

## Daily Start Commands

If setup is already done:

Backend:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\frontend\webapp
npm run dev
```

## Common Issues

### `npm install` fails in `frontend/`

Use:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\frontend\webapp
```

`frontend/` is not the React app root.

### Login/register requests fail with `OPTIONS ... 400`

That is usually a CORS mismatch. Make sure `backend/.env` includes:

```env
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```

Then restart the backend.

### PowerShell blocks venv activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Useful Checks

Backend health:

```bash
curl http://127.0.0.1:8000/
```

Targeted backend tests:

```bash
backend/.venv/bin/pytest backend/tests/test_conversations.py
```

## Main Frontend/Backend Flows

- auth: register, login, refresh persistence
- home: dashboard hydration from backend
- journal: preview + save text check-in
- history: recent entries and timeline
- wrapups: weekly and monthly summaries
- realtime conversation:
  - create session
  - connect websocket
  - send transcript turns
  - receive assistant response
  - end session

## More Detail

- backend docs: [backend/README.md](backend/README.md)
- frontend app: [frontend/webapp/README.md](frontend/webapp/README.md)
