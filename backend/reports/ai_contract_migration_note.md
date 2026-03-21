# AI Contract Migration Note

## Legacy Response Fields

Preview currently exposes legacy top-level AI fields such as:

- `emotion_analysis`
- `risk_level`
- `risk_flags`
- `topic_tags`
- `response_plan`
- `empathetic_response`
- `gentle_suggestion`
- `quote`
- `ai_response`

Processed check-ins currently expose legacy flat AI fields such as:

- `emotion_label`
- `valence_score`
- `energy_score`
- `stress_score`
- `social_need_score`
- `confidence`
- `dominant_signals`
- `response_mode`
- `language`
- `primary_emotion`
- `secondary_emotions`
- `empathetic_response`
- `gentle_suggestion`
- `quote_text`
- `topic_tags`
- `risk_level`
- `risk_flags`
- `response_metadata`

## New Additive `ai` Object

Preview and processed check-ins now also expose a top-level additive `ai` object:

- `ai.emotion`
- `ai.risk`
- `ai.topics`
- `ai.response`
- `ai.state`
- `ai.strategy`
- `ai.memory`

This object is built from the shared companion pipeline outputs where available:

- `emotion_analysis`
- `normalized_state`
- `support_strategy`
- `memory_summary`
- `insight_features`
- `response_plan`

For older or partial processed entries, the contract builder falls back to the stable legacy fields and returns a partial `ai` object instead of failing.

## Mapping Strategy

- `ai.emotion` normalizes the user-facing emotional reading from `emotion_analysis`
- `ai.risk` normalizes `risk_level` and `risk_flags`
- `ai.topics` normalizes `topic_tags`
- `ai.response` groups rendered response data and the stable subset of `response_plan`
- `ai.state` promotes normalized state fields from `normalized_state`
- `ai.strategy` promotes safe support strategy fields from `support_strategy`
- `ai.memory` promotes safe memory summary and insight fields from `memory_summary` and `insight_features`

The contract intentionally does not expose unstable internal fields such as raw render-context evidence spans or provider-specific debug payloads.

## Frontend Migration

Recommended gradual migration:

1. Continue reading legacy fields for current screens.
2. Start reading `ai.*` for all new frontend work.
3. Prefer `ai` as the source of truth whenever both are present.
4. Only remove frontend dependence on legacy flat fields after one explicit cleanup phase.

## Likely Future Deprecation Candidates

Not deprecated yet, but likely candidates later:

- preview: `emotion_analysis`, `risk_level`, `risk_flags`, `topic_tags`, `response_plan`, `empathetic_response`, `gentle_suggestion`, `quote`, `ai_response`
- processed check-ins: flat emotion/risk/response fields that now map directly into `ai.*`

This phase is additive only. No legacy fields were removed or renamed.
