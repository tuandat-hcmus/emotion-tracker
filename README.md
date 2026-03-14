# Emotion Voice Backend MVP

Backend MVP for a voice journal / emotional companion app built with FastAPI, SQLAlchemy, and SQLite/PostgreSQL. This phase adds Alembic migrations, PostgreSQL support, production-friendly health endpoints, configurable CORS, and lightweight structured API errors.

## Features

- Health check endpoint
- Liveness and readiness endpoints
- Auth register/login/me endpoints
- Audio upload endpoint
- Journal entry processing endpoint
- Journal entry async processing endpoint
- Journal entry reprocess endpoint
- Journal entry delete endpoint
- Journal entry detail endpoint
- Journal processing attempts endpoint
- Current user profile endpoint
- Current user preferences endpoints
- Frontend-ready home dashboard endpoint
- Daily check-in status endpoint
- Calendar / emotion history endpoint
- Weekly and monthly wrap-up snapshot endpoints
- Deterministic demo seed script for smoke/manual testing
- Optional dev-only demo seed/reset endpoints
- Richer multi-signal emotion analysis
- Structured empathy planning and response generation
- Dev-friendly text-only response preview endpoint
- User tree state endpoint
- User tree timeline endpoint
- User summary endpoint
- User journal history endpoint
- Crisis resources endpoint
- Local audio storage in `uploads/`
- SQLite persistence
- PostgreSQL support via `DATABASE_URL`
- Alembic migrations
- Mock or provider-based speech-to-text
- Heuristic emotion analysis
- Heuristic topic tagging
- Mock or provider-based empathetic response generation
- Rule-based safety detection
- Persistent tree state updates per processed check-in
- Curated quote selection tied to mood and `quote_opt_in`
- Heuristic weekly/monthly wrap-up snapshot generation
- Idempotent tree recomputation for reprocess and delete flows
- Processing audit attempts per run
- Upload validation for extension, MIME type, and size
- JWT bearer authentication with optional dev bypass
- User profile and preference storage
- Configurable CORS
- Structured API errors for common failures
- Pytest API coverage

## Project Structure

```text
app/
  api/
  core/
  db/
  models/
  schemas/
  services/
uploads/
```

## Setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
alembic upgrade head
```

4. Run the app:

```bash
uvicorn app.main:app --reload
```

5. Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Run Tests

```bash
pytest
```

## Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback one migration:

```bash
alembic downgrade -1
```

## Environment

The app reads configuration from `.env`:

```env
APP_NAME=Emotion Voice Backend
DATABASE_URL=sqlite:///./app.db
DB_ECHO=false
AUTO_CREATE_TABLES_FOR_DEV=true
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:5173
ENABLE_DEV_SEED_ENDPOINTS=false
UPLOADS_DIR=uploads
USE_MOCK_STT=true
USE_MOCK_RESPONSE=true
STT_PROVIDER=mock
RESPONSE_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=gpt-4o-mini
OPENAI_AUDIO_MODEL=gpt-4o-mini-transcribe
OPENAI_REQUEST_TIMEOUT_SECONDS=30
MAX_UPLOAD_MB=20
ALLOWED_AUDIO_EXTENSIONS=.wav,.mp3,.m4a,.ogg,.webm
JWT_SECRET_KEY=dev-secret-change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
AUTH_OPTIONAL_FOR_DEV=true
```

Database examples:
- SQLite local dev: `sqlite:///./app.db`
- PostgreSQL: `postgresql+psycopg://postgres:postgres@localhost:5432/emotion`

Provider notes:
- `mock` mode works without any external API key and is the default local-development path.
- `openai` mode is optional and only used when `STT_PROVIDER=openai` or `RESPONSE_PROVIDER=openai`.
- Real provider mode requires `OPENAI_API_KEY` and the `openai` Python package.
- If a real provider call fails during processing, the journal entry is marked `failed` and the API returns a clear error response.

Auth notes:
- `AUTH_OPTIONAL_FOR_DEV=true` keeps local/dev flows easy: existing protected routes still work without a bearer token.
- `AUTH_OPTIONAL_FOR_DEV=false` enables strict mode: protected routes require a valid JWT and enforce ownership.
- Even in optional-dev mode, if a bearer token is present the backend uses that authenticated user for ownership decisions.

Startup notes:
- Production/postgres flow should run `alembic upgrade head` before starting the app.
- SQLite local dev can still auto-create tables when `AUTO_CREATE_TABLES_FOR_DEV=true`.
- Tests continue to use temporary SQLite databases and do not require PostgreSQL.

## API Summary

- `GET /` health check
- `GET /health/live` liveness endpoint
- `GET /health/ready` readiness endpoint with DB connectivity check
- `POST /v1/auth/register` register with email and password
- `POST /v1/auth/login` receive JWT bearer token
- `GET /v1/auth/me` fetch the authenticated user
- `GET /v1/me` fetch current profile and preference summary
- `PATCH /v1/me` update `display_name`
- `GET /v1/me/preferences` fetch current preferences
- `PUT /v1/me/preferences` create or update preferences
- `GET /v1/me/home` fetch an aggregated home/dashboard payload for the authenticated user
- `GET /v1/me/checkin-status?date=YYYY-MM-DD` fetch daily check-in completion and latest entry signals
- `GET /v1/me/calendar?days=30` fetch one daily mood/calendar item per day in ascending date order, including zero-entry days
- `GET /v1/me/wrapups/weekly/latest` fetch the latest weekly wrap-up snapshot, generating the current week on demand if missing
- `GET /v1/me/wrapups/monthly/latest` fetch the latest monthly wrap-up snapshot, generating the current month on demand if missing
- `POST /v1/me/wrapups/regenerate` regenerate and upsert a weekly or monthly wrap-up snapshot for an optional anchor date
- `POST /v1/me/respond-preview` preview emotion analysis, response planning, and supportive output from plain text without persisting a check-in
- `POST /v1/dev/seed-demo-data` dev-only endpoint to create deterministic demo data when `ENABLE_DEV_SEED_ENDPOINTS=true`
- `POST /v1/dev/reset-demo-data` dev-only endpoint to remove the demo user/data when `ENABLE_DEV_SEED_ENDPOINTS=true`
- `POST /v1/checkins/upload` upload audio with `file`, `user_id`, `session_type`
- `POST /v1/checkins/{entry_id}/process` process a journal entry with optional `override_transcript`
- `POST /v1/checkins/{entry_id}/process-async` accept a journal entry for background processing
- `POST /v1/checkins/{entry_id}/reprocess` rerun processing for a processed or failed entry
- `DELETE /v1/checkins/{entry_id}` delete a journal entry and remove its audio file if present
- `GET /v1/checkins/{entry_id}` fetch a journal entry
- `GET /v1/checkins/{entry_id}/attempts` fetch processing attempts newest first
- `GET /v1/users/{user_id}/tree` fetch the user tree state
- `GET /v1/users/{user_id}/tree/timeline?days=30` fetch daily tree/chart data in ascending date order
- `GET /v1/users/{user_id}/summary?days=30` fetch structured recent summary metrics
- `GET /v1/users/{user_id}/entries` fetch paginated journal history with optional filters
- `GET /v1/resources/crisis?country=VN` fetch lightweight static crisis resources

Journal history query params:
- `limit` default `20`, max `100`
- `offset` default `0`
- `session_type` optional
- `status` optional
- `from_date` optional `YYYY-MM-DD`
- `to_date` optional `YYYY-MM-DD`

## Feature Notes

- Registration stores hashed passwords and login returns JWT bearer tokens.
- Common error responses now include `error.code`, `error.message`, and `error.details` while preserving `detail` for compatibility.
- User preferences are stored separately with defaults for locale, timezone, reminders, and daily check-in goals.
- `PUT /v1/me/preferences` is idempotent and creates defaults on first use if needed.
- `GET /v1/me/home` is intended as the frontend home-screen payload so the app can render user, preference, today, tree, trend, quote, and wrap-up metadata from one call.
- `GET /v1/me/checkin-status` resolves the requested day in the user's saved timezone when valid and falls back to UTC if the timezone value is invalid.
- `GET /v1/me/calendar` builds directly from journal entries only, returns one item per requested day, and uses semantic mood tokens such as `bright`, `calm`, `neutral`, `low`, and `heavy` instead of raw UI colors.
- Quotes are local curated templates only. If `quote_opt_in` is `false`, the home endpoint returns `"quote": null`. High-risk states use calm/supportive quote variants only.
- Emotion analysis now uses deterministic multi-signal inference from transcript text and weighs cues such as loneliness, emptiness, overwhelm, frustration, exhaustion, gratitude, pride, calm, uncertainty, and mixed-contrast phrasing. It still returns additive fields such as `social_need_score`, `confidence`, `dominant_signals`, and `response_mode`.
- `response_mode` is a stable backend hint for tone selection. Current values include `validating_gentle`, `grounding_soft`, `supportive_reflective`, `celebratory_warm`, `low_energy_comfort`, and `high_risk_safe`.
- Supportive response generation is separated into empathy, optional gentle suggestion, and optional quote. The mock path stays deterministic but now varies tone more naturally for lonely, overwhelmed, frustrated, positive, and mixed states. Existing `ai_response` is still populated for backward compatibility as a combined legacy field.
- `POST /v1/me/respond-preview` reuses the real analysis/planning/response services but does not write journal history, mutate tree state, or create wrap-up data.
- Mock mode remains deterministic and template-based for tests and local development. Provider mode can still be enabled for response generation and is normalized into the same structured response contract.
- Transcript-only emotion inference is still heuristic and limited by what the user explicitly says. It should be treated as supportive product behavior, not as diagnosis, therapy, or clinical assessment.
- Wrap-up generation is deterministic, heuristic/template-based, and non-LLM for now. Weekly periods use Monday-Sunday boundaries and monthly periods use calendar-month boundaries.
- If no stored wrap-up exists yet, the latest weekly/monthly endpoints generate the current period on demand and persist it.
- Wrap-up snapshots are stored in `wrapup_snapshots` and upserted per `user_id + period_type + period_start + period_end`.
- Wrap-ups use processed entries only. With little or no data they still return a structured payload with zero counts, null highlights where appropriate, and a template closing message.
- Demo data seeding is deterministic by default, creates one documented demo user, builds about 30 days of processed entries with some no-entry days and heavier days, recomputes tree state, and generates wrap-up snapshots for smoke testing.
- Dev seed/reset endpoints are local-development helpers only. Leave `ENABLE_DEV_SEED_ENDPOINTS=false` outside dev/test usage.
- `GET /v1/resources/crisis` is a lightweight static product-support endpoint and not a claim of complete or medical guidance.
- This backend provides supportive wellness-oriented reflections only. It does not provide diagnosis, crisis assessment, or therapy.
- Safety detection is rule-based and stores `risk_level` plus `risk_flags` on each processed journal entry.
- High-risk and medium-risk transcripts return supportive safety-oriented messages instead of the normal empathetic response.
- Tree state is stored persistently in `tree_states` and each processed check-in writes derived `tree_state_events`.
- Tree updates are handled by recomputing from processed entries for that user, so reprocessing the same entry does not double-count growth and deleting an entry rebalances the tree cleanly.
- Summary responses are structured JSON only and do not use LLM-generated text.
- Uploads are rejected before saving if the extension is unsupported, the MIME type is obviously invalid, or the file exceeds `MAX_UPLOAD_MB`.
- Allowed default upload formats are `.wav`, `.mp3`, `.m4a`, `.ogg`, and `.webm`.
- STT and response generation now use provider-based services so mock mode and optional real-provider mode share the same processing flow.
- Every sync process, async process, and reprocess run creates a `processing_attempts` record with provider names, trigger type, status, and optional error message.
- `process-async` uses FastAPI `BackgroundTasks`, so it is lightweight and local-process only. It is suitable for MVP usage but not durable across restarts or multi-worker deployments.
- Flexible list fields such as topics and risk flags are stored as JSON strings in SQLite text columns.
- Alembic is now the primary schema-management path.
- `create_all` is only used for local SQLite dev bootstrap when `AUTO_CREATE_TABLES_FOR_DEV=true`.
- CORS is disabled by default unless `BACKEND_CORS_ORIGINS` is configured.

## Auth Examples

Register:

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"secret123","display_name":"Demo"}'
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"secret123"}'
```

Authenticated request:

```bash
curl http://127.0.0.1:8000/v1/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Respond preview:

```bash
curl -X POST http://127.0.0.1:8000/v1/me/respond-preview \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Mình hơi căng vì deadline công việc nhưng vẫn cố gắng."}'
```

Upload behavior:
- In strict auth mode, authenticated uploads ignore the form `user_id` and use the token owner.
- In optional dev mode with no token, uploads preserve the existing form-based `user_id` behavior for local workflows.

## Running Locally

SQLite dev workflow:

```bash
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

If you want the app to bootstrap tables for SQLite dev without running migrations first:

```env
AUTO_CREATE_TABLES_FOR_DEV=true
```

PostgreSQL workflow:

```bash
set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/emotion
alembic upgrade head
uvicorn app.main:app --reload
```

## Demo Seed Data

Demo credentials:
- Email: `demo@example.com`
- Password: `demo123456`

Seed deterministic demo data:

```bash
python scripts/seed_demo_data.py --days 30 --email demo@example.com --password demo123456
```

Reset only:

```bash
python scripts/seed_demo_data.py --reset-only --email demo@example.com
```

Reset first, then reseed:

```bash
python scripts/seed_demo_data.py --reset --days 30
```

Enable dev-only seed endpoints:

```env
ENABLE_DEV_SEED_ENDPOINTS=true
```

Dev endpoint examples:

```bash
curl -X POST http://127.0.0.1:8000/v1/dev/seed-demo-data \
  -H "Content-Type: application/json" \
  -d '{"days":30,"email":"demo@example.com","password":"demo123456"}'

curl -X POST http://127.0.0.1:8000/v1/dev/reset-demo-data \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com"}'
```

Exact local workflow:

```bash
alembic upgrade head
python scripts/seed_demo_data.py --reset --days 30
uvicorn app.main:app --reload
pytest
```
