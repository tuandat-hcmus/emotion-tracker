# Emotion Tracker

This repository is now split so backend and frontend work can happen in parallel:

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

## Frontend

Your collaborator can add the frontend app inside `frontend/` without touching the backend layout.
