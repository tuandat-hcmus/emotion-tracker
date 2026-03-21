# AI Pipeline Migration Note

## Old Path

Production-like request flow:

`/v1/me/respond-preview`
-> `app/services/ai_support_service.py`
-> `analyze_emotion(...)`
-> `build_response_plan(...)`
-> `generate_supportive_response(...)`

English demo flow:

`/v1/demo/ai-core`
-> `app/services/en_demo_service.py`
-> demo-only render-context detection
-> demo-only normalized state / support strategy / memory summary
-> renderer

## New Shared Path

First-phase shared reasoning flow:

1. emotion inference via `analyze_emotion(...)`
2. render-context detection via `app/services/companion_core/render_context.py`
3. normalized state / memory summary / insight features / support strategy via `app/services/companion_core/pipeline.py`
4. response rendering via existing `response_service.py`

`ai_support_service.py` now uses the shared companion pipeline before rendering.

`en_demo_service.py` now uses the same shared companion pipeline and only keeps demo-specific emotion adjustments and renderer-debug behavior.

## Not Yet Unified

- `vi_demo_service.py` still uses the older direct path.
- persistent memory storage is not implemented yet; production wiring should use a non-persistent store until a DB-backed implementation is added.
- public API contracts remain backward-compatible; the richer normalized state is currently exposed in demo responses and internal metadata, not yet promoted as a new external contract for every endpoint.
