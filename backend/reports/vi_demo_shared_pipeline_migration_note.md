# VI Demo Shared Pipeline Migration Note

## Before

`build_vi_demo_payload()` orchestrated the Vietnamese demo path directly:

- `analyze_emotion()`
- `_maybe_adjust_short_event_emotion()`
- `build_response_plan()`
- `render_supportive_response()` or local template fallback

That meant the VI demo path duplicated reasoning orchestration that preview/check-in and the English demo already handled through `companion_core`.

## Now

`build_vi_demo_payload()` uses `build_companion_pipeline()` as its shared backend orchestration layer.

Shared pipeline pieces now used by the Vietnamese demo:

- render context detection
- normalized state
- memory summary
- insight features
- support strategy
- response plan

The Vietnamese demo now maps those shared outputs into the existing demo response shape and also populates `ai_core`, matching the English demo more closely.

## Still Language-Specific

The following remain intentionally Vietnamese-specific:

- `_maybe_adjust_short_event_emotion()`
  - this is still a narrow VI-specific postprocessor for very short relationship/health updates
- `_build_demo_response_text()`
  - this remains the local Vietnamese template renderer for non-Gemini fallback behavior

## Scope Left For Later

- unify Vietnamese demo rendering patterns further with English where that is product-safe
- decide whether the VI short-event adjustment should move into a shared language-adapter layer
- align any remaining demo-only contract differences without changing preview/check-in contracts
