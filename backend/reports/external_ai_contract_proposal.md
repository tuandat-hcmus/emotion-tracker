# External AI Contract Proposal

## Current Shapes

### Preview: `POST /v1/me/respond-preview`

Current response exposes:

- `emotion_analysis`
- `topic_tags`
- `risk_level`
- `risk_flags`
- `response_plan`
- `empathetic_response`
- `gentle_suggestion`
- `quote`
- `ai_response`

The new shared companion pipeline already computes additional internal state, but preview does not expose it yet:

- `render_context`
- `normalized_state`
- `support_strategy`
- `memory_summary`
- `insight_features`

### Processed check-in: `POST /v1/checkins/{entry_id}/process`

Current response is flatter and mixes storage-oriented and AI-oriented fields:

- check-in metadata: `entry_id`, `status`, `user_id`, `session_type`, timestamps, file path
- AI fields: `ai_response`, `emotion_label`, `valence_score`, `energy_score`, `stress_score`, `social_need_score`, `confidence`, `dominant_signals`, `response_mode`, `language`, `primary_emotion`, `secondary_emotions`, `source`, `raw_model_labels`, `provider_name`, `empathetic_response`, `gentle_suggestion`, `quote_text`, `topic_tags`, `risk_level`, `risk_flags`
- catch-all metadata bucket: `response_metadata`

The shared companion outputs are currently preserved inside `response_metadata` for backward-aware storage and retrieval.

### Demo: `POST /v1/demo/ai-core`

Current response is already closer to a future typed contract:

- top-level request/result fields: `input_text`, `language`, `topic_tags`, `risk_level`, `risk_flags`
- nested `emotion`
- nested `support`
- nested `ai_core.normalized_state`
- nested `ai_core.support_strategy`
- nested `ai_core.memory_summary`
- nested `ai_core.insight_features`

## Proposed Stable Contract

Introduce one shared top-level `ai` object for preview, processed check-ins, and demo:

```json
{
  "ai": {
    "emotion": {
      "label": "lo lắng",
      "primary_emotion": "anxiety",
      "secondary_emotions": ["sadness"],
      "valence": -0.28,
      "energy": 0.44,
      "stress": 0.58,
      "social_need": 0.34,
      "confidence": 0.46,
      "dominant_signals": ["anxiety_activation", "connection_need"],
      "response_mode": "supportive_reflective",
      "language": "vi",
      "source": "text",
      "provider_name": "heuristic_fallback",
      "raw_model_labels": ["anxiety", "sadness"]
    },
    "risk": {
      "level": "low",
      "flags": []
    },
    "topics": ["relationships", "health"],
    "response": {
      "plan": {
        "opening_style": "reflective",
        "acknowledgment_focus": "mixed_state",
        "suggestion_allowed": true,
        "suggestion_style": "small_reflective",
        "quote_allowed": false,
        "avoid_advice": true,
        "tone": "steady_reflective",
        "max_sentences": 3
      },
      "empathetic_text": "...",
      "suggestion_text": null,
      "quote": null,
      "composed_text": "..."
    },
    "state": {
      "emotion_owner": "user",
      "social_context": "solo",
      "event_type": "uncertain_mixed_state",
      "concern_target": null,
      "uncertainty": 0.54
    },
    "strategy": {
      "support_focus": "user",
      "strategy_type": "supportive_reflective",
      "suggestion_budget": "minimal",
      "personalization_tone": "gentle",
      "response_goal": "feel_heard",
      "rationale": []
    },
    "memory": {
      "summary": null,
      "insight_features": null
    }
  }
}
```

## Compatibility Strategy

Phase 1:

- Keep existing preview fields unchanged.
- Keep existing processed check-in fields unchanged.
- Add optional `ai` object alongside legacy fields.
- Populate `ai` from the shared companion pipeline already used internally.

Phase 2:

- Move frontend consumers to `ai.*`.
- Keep old preview fields as adapters for one release window.
- Keep processed check-in flat fields populated from `ai.emotion` and `ai.response`.

Phase 3:

- Deprecate duplicate flat AI fields from preview and processed check-in.
- Keep storage-only fields outside `ai`.

## Frontend Impact

Benefits:

- preview, processed check-in, and demo can render from one consistent AI shape
- frontend stops reverse-engineering `response_metadata`
- normalized state and strategy become first-class, typed API data

Migration impact:

- existing preview UI can keep reading legacy fields until it is switched
- processed check-in UI can gradually replace flat AI fields with `ai.*`
- demo UI is already closest to the target shape and mostly needs renaming/alignment
