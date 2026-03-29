# Emotion Tracker - Project Overview

## Current Status

The project is **complete and functional**. It is a full-stack emotional wellness journaling application with multi-modal input (text + voice), AI-powered emotion analysis, and a rich interactive UI. The most recent work added calendar integration and weekly/monthly recap features. The codebase is clean (no TODOs/FIXMEs found), with 13 commits on `main`.

---

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (webapp/)                     │
│           React 19 + React Router 7 + TypeScript            │
│                    Tailwind CSS + shadcn/ui                  │
│          Three.js (SoulTree 3D visualization)               │
│                                                             │
│  AuthContext ─── JWT token in localStorage                   │
│  SoulForestContext ─── tree state hydration                  │
│  API Client ─── fetch + WebSocket + mock fallback           │
└───────────────┬──────────────────────┬──────────────────────┘
                │ REST (HTTP)          │ WebSocket
                ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (backend/)                       │
│                  FastAPI + SQLAlchemy (sync)                 │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Auth     │  │ Check-in     │  │ Conversation       │    │
│  │ (JWT)    │  │ Pipeline     │  │ (WebSocket)        │    │
│  └──────────┘  └──────┬───────┘  └─────────┬──────────┘    │
│                       │                     │               │
│              ┌────────▼─────────────────────▼────────┐      │
│              │         SERVICE LAYER                 │      │
│              │                                       │      │
│              │  ┌─────────────┐  ┌───────────────┐   │      │
│              │  │ AI Core     │  │ Companion Core│   │      │
│              │  │ (HF Model)  │  │ (Strategy +   │   │      │
│              │  │ XLM-RoBERTa │  │  Memory +     │   │      │
│              │  │ 7-label     │  │  Insight)     │   │      │
│              │  └─────────────┘  └───────────────┘   │      │
│              │                                       │      │
│              │  ┌─────────────┐  ┌───────────────┐   │      │
│              │  │ Safety &    │  │ Response      │   │      │
│              │  │ Risk Detect │  │ Renderer      │   │      │
│              │  └─────────────┘  │ (Gemini API)  │   │      │
│              │                   └───────────────┘   │      │
│              │  ┌─────────────┐  ┌───────────────┐   │      │
│              │  │ Tree State  │  │ Wrapup &      │   │      │
│              │  │ Service     │  │ Calendar      │   │      │
│              │  └─────────────┘  └───────────────┘   │      │
│              └───────────────────────────────────────┘      │
│                              │                              │
│              ┌───────────────▼───────────────┐              │
│              │  OpenAI Whisper (STT, optional)│              │
│              └───────────────────────────────┘              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  PostgreSQL   │
                    │  (9 tables)   │
                    └───────────────┘
```

### Processing Pipeline (Text Check-in)

```
User Input → Normalize → Load Recent Context (last 2 entries)
  → Local HF Emotion Inference (XLM-RoBERTa, 7-label)
  → Deterministic Response Planning (safety-aware)
  → Render Response (Gemini or mock)
  → Postcheck (evidence-bounded validation)
  → Persist to DB
```

### Key Architectural Rules

1. **Local HF model is sole source of truth** for emotion classification
2. **Gemini is renderer-only** -- generates text from emotion + plan, never re-infers emotion
3. **Canonical 7-label schema**: anger, disgust, fear, joy, sadness, surprise, neutral
4. **Deterministic backend** owns: state normalization, safety, response planning, policy
5. **Postcheck enforces** evidence-bounded output
6. **Fallback mode**: Frontend works offline with mock API + localStorage

---

## App Functions (What Users Can Do)

| Feature | Description |
|---|---|
| **Register / Login** | Email + password authentication with JWT |
| **Dashboard Home** | Overview: tree visualization, today's check-ins, trend, motivational quote, wrapup metadata |
| **Text Check-in** | Write a journal entry; get emotion analysis + empathetic AI response |
| **Voice Check-in** | Record audio; speech-to-text transcription then same emotion pipeline |
| **Real-time Chat** | WebSocket conversation with streaming audio/text and live AI responses |
| **Journal History** | Timeline view of past entries with pagination |
| **Calendar View** | 30-day grid showing daily emotion summaries |
| **Weekly/Monthly Recap** | AI-generated summaries with trends, triggers, streaks, insights |
| **SoulTree Visualization** | 3D animated tree reflecting emotional wellness (vitality, stage, weather) |
| **Preferences** | Configure locale, timezone, reminders, tree type, check-in goals |
| **Crisis Resources** | Access to crisis hotlines by country (VN/US) |

---

## Frontend Routes (UI Endpoints)

| Route | Page | Description |
|---|---|---|
| `/` | Landing Page | Welcome screen for unauthenticated users |
| `/login` | Login | Email/password sign-in |
| `/register` | Register | Account creation |
| `/app` | App Index | Redirects to `/app/home` |
| `/app/home` | Dashboard Home | Main dashboard with tree, stats, check-in status |
| `/app/journal` | Journal | Text/voice check-in creation + history timeline |
| `/app/chat` | Chat | Real-time conversation sessions |

---

## Backend API Endpoints

### Authentication (`/v1/auth`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Create account (email, password, display_name) |
| POST | `/login` | Sign in, returns JWT + user object |
| GET | `/me` | Get current authenticated user |

### Check-ins (`/v1/checkins`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/text` | Create text check-in (sync emotion analysis + response) |
| POST | `/upload` | Upload audio file for voice check-in |
| POST | `/{entry_id}/process` | Process uploaded audio synchronously |
| POST | `/{entry_id}/process-async` | Process audio asynchronously (returns 202) |
| POST | `/{entry_id}/reprocess` | Reprocess already-processed entry |
| DELETE | `/{entry_id}` | Delete check-in entry and audio |
| GET | `/{entry_id}` | Fetch single check-in details |
| GET | `/{entry_id}/attempts` | List processing attempts for entry |

### Conversations (`/v1/conversations`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Start new conversation session |
| GET | `/sessions` | List user's sessions (paginated) |
| GET | `/sessions/{session_id}` | Get session details |
| GET | `/sessions/{session_id}/turns` | Get conversation turns (paginated) |
| POST | `/sessions/{session_id}/end` | End conversation session |
| WebSocket | `/ws/{session_id}` | Real-time voice/text streaming |

### User Profile (`/v1/me`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Get user profile with preferences |
| PATCH | `/` | Update display_name |
| GET | `/preferences` | Get user preferences |
| PUT | `/preferences` | Update preferences |
| GET | `/home` | Dashboard hydration (user, tree, checkins, trend, quote) |
| GET | `/checkin-status` | Check-in status for specific date |
| GET | `/calendar` | 30-day calendar with daily emotion summaries |
| GET | `/wrapups/weekly/latest` | Latest weekly summary |
| GET | `/wrapups/monthly/latest` | Latest monthly summary |
| POST | `/wrapups/regenerate` | Regenerate wrapup for custom period |
| POST | `/respond-preview` | Preview emotion response without saving |

### User History (`/v1/users`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/{user_id}/tree` | Get user's tree state |
| GET | `/{user_id}/summary` | User summary stats (emotion counts, trends, triggers) |
| GET | `/{user_id}/entries` | List journal entries (paginated) |

### Other

| Method | Endpoint | Description |
|---|---|---|
| POST | `/v1/demo/ai-core` | Demo emotion analysis (no auth) |
| GET | `/v1/demo/ai-core/weekly-insight` | Demo weekly insight |
| POST | `/v1/dev/seed-demo-data` | Seed demo data |
| POST | `/v1/dev/reset-demo-data` | Reset demo data |
| GET | `/v1/resources/crisis` | Crisis resources by country |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness check (includes DB) |

---

## Backend Models (Database Schema)

### User
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | String | Unique |
| password_hash | String | |
| display_name | String | |
| is_active | Boolean | Default: true |
| created_at | DateTime | |
| updated_at | DateTime | |

### UserPreference
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Unique FK → User |
| locale | String | Default: "vi" |
| timezone | String | Default: "Asia/Bangkok" |
| quote_opt_in | Boolean | |
| reminder_enabled | Boolean | |
| reminder_time | String | |
| preferred_tree_type | String | |
| checkin_goal_per_day | Integer | |

### JournalEntry
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Indexed FK → User |
| session_type | String | Default: "free" |
| audio_path | String | Nullable |
| raw_text | String | Nullable |
| transcript_text | String | Nullable |
| transcript_confidence | Float | Nullable |
| processing_status | String | "uploaded" / "processing" / "processed" / "failed" |
| emotion_label | String | Primary emotion |
| valence_score | Float | |
| energy_score | Float | |
| stress_score | Float | |
| social_need_score | Float | |
| emotion_confidence | Float | |
| dominant_signals_text | String | JSON-encoded |
| topic_tags_text | String | JSON-encoded |
| risk_level | String | low / medium / high |
| risk_flags_text | String | JSON-encoded |
| response_mode | String | |
| empathetic_response | String | |
| gentle_suggestion | String | |
| quote_text | String | |
| ai_response | String | |
| response_metadata_text | String | JSON-encoded |
| created_at | DateTime | |
| updated_at | DateTime | |

### ProcessingAttempt
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| entry_id | UUID | FK → JournalEntry |
| user_id | UUID | |
| trigger_type | String | manual / async / reprocess |
| provider_stt | String | |
| provider_response | String | |
| status | String | |
| used_override_transcript | Boolean | |
| error_message | String | Nullable |
| started_at | DateTime | |
| finished_at | DateTime | Nullable |

### TreeState
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Unique FK → User |
| vitality_score | Float | Default: 50 |
| streak_days | Integer | |
| current_stage | String | Default: "sapling" |
| leaf_state | String | |
| weather_state | String | |
| last_checkin_date | Date | Nullable |
| created_at | DateTime | |
| updated_at | DateTime | |

### TreeStateEvent
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | |
| event_type | String | |
| event_data | String | JSON-encoded |
| created_at | DateTime | |

### ConversationSession
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Indexed FK → User |
| status | String | Default: "active" |
| started_at | DateTime | |
| ended_at | DateTime | Nullable |

### ConversationTurn
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| session_id | UUID | Indexed FK → ConversationSession |
| role | String | "user" / "assistant" |
| text | String | |
| audio_path | String | Nullable |
| emotion_snapshot | String | JSON-encoded |
| state_snapshot | String | JSON-encoded |
| created_at | DateTime | |

### WrapupSnapshot
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Indexed FK → User |
| period_type | String | "week" / "month" |
| period_start | Date | |
| period_end | Date | |
| payload_text | String | JSON of full wrapup data |
| generated_at | DateTime | |
| created_at | DateTime | |
| updated_at | DateTime | |
| | | Unique: (user_id, period_type, period_start, period_end) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, React Router 7, TypeScript, Tailwind CSS, shadcn/ui, Three.js |
| Backend | Python, FastAPI, SQLAlchemy (sync), Pydantic, Alembic |
| Database | PostgreSQL (9 tables, 5 migrations) |
| AI/ML | Hugging Face XLM-RoBERTa (local emotion model), Google Gemini (response renderer) |
| STT | OpenAI Whisper (optional, mock available) |
| Auth | JWT (access tokens) |
| Infra | Docker Compose (local dev) |
