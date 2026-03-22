# Frontend

The current frontend app lives in:

```text
frontend/webapp
```

Do not run `npm install` from `frontend/`.

## Start the Frontend

Windows PowerShell:

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\frontend\webapp
npm install
Copy-Item .env.example .env
npm run dev
```

Bash:

```bash
cd frontend/webapp
npm install
cp .env.example .env
npm run dev
```

## Required Env

`frontend/webapp/.env`

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## App URLs

- frontend: `http://localhost:5173`
- backend: `http://127.0.0.1:8000`

## Notes

- the frontend is a React Router + TypeScript app
- the backend must be running for auth, journal, history, wrapups, and realtime conversation
- if login/register fails with an `OPTIONS` error, check backend CORS in `backend/.env`
