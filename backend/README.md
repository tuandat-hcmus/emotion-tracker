# Emotion Backend

## Overview

This backend powers an emotional wellness journaling product built on FastAPI, PostgreSQL, sync SQLAlchemy, and Alembic.

Current architectural rules:
- the local Hugging Face model is the only source of truth for emotion detection
- the frontend-facing emotion schema is always the canonical 7-label set:
  - `anger`
  - `disgust`
  - `fear`
  - `joy`
  - `sadness`
  - `surprise`
  - `neutral`
- deterministic backend services own:
  - state normalization
  - safety
  - response planning
  - response policy
- Gemini is renderer only
- postcheck enforces evidence-bounded output and rejects unsupported specifics

The system is not designed as a full autonomous agent. Gemini must not reinterpret history, re-infer emotion, or invent hidden facts.

## Current Processing Flows

### Text Check-in

`POST /v1/checkins/text`

Flow:
1. validate and normalize text
2. load lightweight recent context from stored snapshots
3. run local emotion inference on the current text
4. build deterministic companion state and response plan
5. render the final supportive response
6. run postcheck
7. persist transcript, snapshots, and response fields

### Voice Check-in

`POST /v1/checkins/upload`
`POST /v1/checkins/{entry_id}/process`

Flow:
1. accept and store audio reference
2. run STT
3. normalize transcript
4. send transcript through the same downstream text pipeline
5. persist transcript, snapshots, and response fields

Voice does not have a separate emotion pipeline. STT only produces transcript text.

## Stable Boundaries

- emotion inference: local HF only
- companion state and strategy: deterministic backend services
- planning and policy: deterministic backend services
- rendering: Gemini or mock/template renderer
- enforcement: postcheck
- frontend contract: canonical 7-label schema

## Response Architecture

Current response layers:
1. safety layer
2. deterministic planning layer
3. response policy layer
4. renderer layer
5. postcheck layer
6. final API contract shaping

Important behavior:
- English is the default response language unless a supported override is clear
- medium/high-risk inputs bypass normal renderer behavior
- the final response should stay evidence-bounded and abstract unless the transcript supports more specificity

## Main Contracts

Top-level response fields used by check-in and preview flows:
- `emotion_analysis`
- `topic_tags`
- `risk_level`
- `risk_flags`
- `response_plan`
- `empathetic_response`
- `follow_up_question`
- `gentle_suggestion`
- `quote`
- `ai_response`
- `ai`

`emotion_analysis` uses:
- `primary_label`
- `secondary_labels`
- `all_labels`
- `scores`
- `threshold`
- `confidence`
- `provider_name`
- `source`
- `language`
- `valence_score`
- `energy_score`
- `stress_score`
- `social_need_score`
- `response_mode`
- `dominant_signals`
- `context_tags`
- `enrichment_notes`

`ai.emotion` mirrors the same canonical contract.

`ai.state` exposes canonical:
- `primary_label`
- `secondary_labels`

## Persistence and History

Journal entries persist:
- raw text when provided directly
- normalized transcript text
- transcript confidence
- canonical emotion snapshot
- risk snapshot
- response plan snapshot
- normalized state snapshot
- strategy snapshot
- lightweight memory snapshot
- final response fields

History retrieval is intentionally lightweight and frontend-friendly. Recent entry items expose:
- `id`
- `entry_id`
- `status`
- `session_type`
- `source_type`
- `transcript_excerpt`
- `ai_response_excerpt`
- `primary_label`
- `secondary_labels`
- `stress_score`
- `created_at`
- `updated_at`

## Wrapups and Summaries

Weekly and monthly wrapups are generated from persisted journal entries and stored AI snapshots by default. Historical emotion inference is not re-run unless explicitly needed elsewhere.

Derived persisted-data features include:
- dominant emotional patterns
- recurring triggers
- workload/deadline patterns
- positive anchors
- emotional direction trend
- high-stress frequency
- concise summary text

These are produced inside:
- `app/services/wrapup_service.py`
- `app/services/summary_service.py`
- `app/services/journal_service.py`

## Configuration

Common env vars:

```env
DATABASE_URL=postgresql+psycopg://...
EMOTION_MODEL_ENABLED=true
EMOTION_MODEL_DIR=models/artifacts/emotion_xlmr
EMOTION_MODEL_DEVICE=auto
GEMINI_ENABLED=true
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash-lite
RESPONSE_PROVIDER=gemini
USE_MOCK_RESPONSE=false
RESPONSE_DEFAULT_LANGUAGE=en
RESPONSE_USE_STRUCTURED_OUTPUT=true
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

Notes:
- if `GEMINI_API_KEY` is not set and `RESPONSE_PROVIDER=gemini`, response rendering will fail
- low-risk rendering may use Gemini when enabled
- non-low-risk paths still bypass the normal renderer

## Local Development

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ai.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Windows:

```bat
run-dev.bat
```

## Testing

Typical test commands:

```bash
python -m pytest
python -m pytest backend/tests/test_app.py -q
python -m pytest backend/tests/test_ai_core.py -q
python -m pytest backend/tests/test_me_home.py -q
```

Focused coverage already exists for:
- canonical response contracts
- text and voice check-in flows
- duplicate processing safety
- failure-path coherence
- response postcheck behavior
- weekly/monthly wrapup generation

## Guidance For Future Changes

When changing the backend:
- preserve the canonical 7-label frontend emotion contract
- do not let Gemini classify emotion
- keep deterministic logic outside Gemini
- prefer additive changes over broad redesigns
- reuse persisted snapshots before considering historical reprocessing
