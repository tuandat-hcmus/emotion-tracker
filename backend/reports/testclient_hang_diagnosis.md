# TestClient Hang Diagnosis

## Minimal Reproduction

The hang reproduces outside the repo with a trivial FastAPI app:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
def root():
    return {"ok": True}

with TestClient(app) as client:
    client.get("/")
```

Observed behavior in this environment:
- prints before entering `TestClient(...)`
- then hangs before the request completes

The same environment also hangs when tearing down an `anyio.from_thread.start_blocking_portal()` context, which points to the async client runtime layer rather than the backend code.

## Root Cause

This is environment-specific and occurs outside the repository:
- not caused by the app routes
- not caused by the new AI-core package
- reproducible with a one-route FastAPI app
- reproducible around the `anyio` blocking portal lifecycle

## Practical Impact

`backend/tests/test_ai_core.py` and `backend/tests/test_app.py` are blocked here because they rely on `fastapi.testclient.TestClient`.

## Mitigation

The backend code remains importable and the non-HTTP AI-core tests pass.
For this environment specifically, direct service-level smoke scripts are more reliable than `TestClient`-based integration tests.
