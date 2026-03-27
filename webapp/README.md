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
cd C:\Users\admin\Desktop\Project\Emotion\webapp
npm install
Copy-Item .env.example .env
npm run dev
```

### Bash

```bash
cd webapp
npm install
cp .env.example .env
npm run dev
```

## Environment

Create `.env` with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
# Optional: force local fallback mode even if the backend is unavailable
# VITE_ENABLE_API_FALLBACK=true
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
- temporary fallback data is available for login, dashboard, journal, history, calendar, wrapups, and text check-ins when the backend cannot be reached
- fallback mode creates a local demo account from the email you sign in with and persists its data in browser local storage
- realtime voice conversation still requires the backend websocket and is not covered by fallback mode
