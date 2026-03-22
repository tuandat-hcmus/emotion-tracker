# Emotion Webapp

This is the current React frontend for the Emotion product.

Stack:
- React
- TypeScript
- React Router 7
- Vite
- Tailwind-based styling

## Run Locally

### Windows PowerShell

```powershell
cd C:\Users\admin\Desktop\Project\Emotion\frontend\webapp
npm install
Copy-Item .env.example .env
npm run dev
```

### Bash

```bash
cd frontend/webapp
npm install
cp .env.example .env
npm run dev
```

## Environment

Create `.env` with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Available Scripts

```bash
npm run dev
npm run build
npm run typecheck
```

## Notes

- the frontend expects the backend to be available at the URL in `VITE_API_BASE_URL`
- auth, dashboard hydration, journal, wrapups, and realtime conversation all depend on the backend
- if the browser shows CORS errors on login or register, update `BACKEND_CORS_ORIGINS` in `backend/.env` and restart the backend
