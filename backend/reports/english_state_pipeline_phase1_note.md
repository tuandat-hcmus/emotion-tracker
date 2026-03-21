# English state pipeline phase 1 note

## Current weaknesses

- `RenderContext` was too shallow for English relational cases.
- `NormalizedEmotionalState` lacked explicit stance/role detail, so the pipeline could not cleanly represent:
  - concern for another person
  - guilt/responsibility toward another person
  - hurt from romantic rejection
  - recognition/praise from another person
- The shared pipeline did not apply a generic context-alignment pass before normalized state and strategy selection, so the system could carry forward raw label mistakes such as:
  - another person's anger or sadness being treated as the user's emotion
  - relational tension being flattened into generic mixed-state output
- `SupportStrategy` relied mostly on valence/stress/social-context heuristics and did not explicitly align to user stance.

## Proposed phase-1 changes

- Enrich internal state representation with:
  - `user_stance`
  - `relationship_role`
  - field-level confidence signals for owner/target/event/stance
- Improve English render-context detection for:
  - named targets
  - teammate/work relations
  - romantic rejection
  - other-person distress
  - responsibility tension
- Add a thin English-first contextual alignment layer ahead of normalized state construction.
- Align strategy selection to stance/event, not just coarse valence/stress.

## Why this improves reasoning quality

- It fixes the highest-value understanding errors without changing the renderer.
- It preserves the current provider stack and outward API while improving the shared reasoning spine.
- It is deterministic and testable, which is important for English-first regression coverage.

## Implemented now

- Internal schema enrichment in `companion_core.schemas`
- English-first relational/event detection improvements in `companion_core.render_context`
- Contextual alignment pass in `companion_core.contextual_inference`
- Strategy alignment updates in `companion_core.strategy_engine`
- Regression/eval coverage in `backend/tests/test_english_state_eval.py`

## Deferred for later

- Outward API promotion of the richer internal state fields
- Persistent companion memory
- Larger multilingual reasoning redesign
- Model-side structured state generation beyond the current rule/model hybrid
