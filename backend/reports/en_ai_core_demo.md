# English AI Core Demo

Generated from the live English-first AI core demo service path.

## Product Rendering Notes

- The renderer is grounded first in the user's exact text and event, then in structured emotion state.
- Gemini is the preferred renderer for normal low-risk English demo cases.
- Template fallback remains available only for provider failure, schema failure, or explicit safety override.

## Work stress / deadline

**Input**: I've had deadlines piling up for days.

**Emotion provider path used**: `heuristic_fallback`
**Support provider used**: `template_fallback`

**Structured emotion output**

```json
{
  "primary_emotion": "overwhelm",
  "secondary_emotions": [],
  "emotion_label": "căng",
  "valence_score": -0.5,
  "energy_score": 0.82,
  "stress_score": 0.88,
  "confidence": 0.35,
  "provider_name": "heuristic_fallback",
  "response_mode": "grounding_soft"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "From what you shared, the clearest part is this: having deadlines pile up for days can make everything feel tight and crowded. You do not have to pretend it is manageable for it to count as a lot.",
  "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
  "safety_note": null,
  "provider_name": "template_fallback"
}
```

**Debug snapshot**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "I've had deadlines piling up for days.",
    "language": "en",
    "primary_emotion": "overwhelm",
    "secondary_emotions": [],
    "confidence": 0.35,
    "response_mode": "grounding_soft",
    "topic_tags": [
      "work/school"
    ],
    "risk_level": "low",
    "utterance_type": "reflective_checkin",
    "event_type": "deadline_pressure",
    "relationship_target": null,
    "short_event_flag": false,
    "low_confidence_flag": true,
    "evidence_spans": [
      "deadline",
      "deadlines",
      "piling up"
    ],
    "social_context": "work_or_school",
    "concern_target": null,
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

## Loved one sick

**Input**: My girlfriend is sick

**Emotion provider path used**: `en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment`
**Support provider used**: `template_fallback`

**Structured emotion output**

```json
{
  "primary_emotion": "anxiety",
  "secondary_emotions": [
    "sadness",
    "neutral"
  ],
  "emotion_label": "concerned",
  "valence_score": -0.24,
  "energy_score": 0.34,
  "stress_score": 0.44,
  "confidence": 0.44,
  "provider_name": "en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment",
  "response_mode": "supportive_reflective"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "Even from a short update like \"My girlfriend is sick\", it makes sense that something emotionally important is sitting underneath. When your girlfriend is unwell, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to them.",
  "gentle_suggestion": "If it helps, pick one small check-in or one practical thing you can do and let that be enough for now.",
  "safety_note": null,
  "provider_name": "template_fallback"
}
```

**Debug snapshot**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "My girlfriend is sick",
    "language": "en",
    "primary_emotion": "anxiety",
    "secondary_emotions": [
      "sadness",
      "neutral"
    ],
    "confidence": 0.44,
    "response_mode": "supportive_reflective",
    "topic_tags": [
      "relationships",
      "friends",
      "health"
    ],
    "risk_level": "low",
    "utterance_type": "relationship_concern",
    "event_type": "loved_one_unwell",
    "relationship_target": "girlfriend",
    "short_event_flag": true,
    "low_confidence_flag": true,
    "evidence_spans": [
      "girlfriend",
      "sick"
    ],
    "social_context": "romantic_relationship",
    "concern_target": "girlfriend",
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

## Loneliness / left out

**Input**: I keep feeling left out lately, like everyone already has their people.

**Emotion provider path used**: `en_canonical_emotion+heuristic_fallback`
**Support provider used**: `template_fallback`

**Structured emotion output**

```json
{
  "primary_emotion": "anxiety",
  "secondary_emotions": [
    "neutral",
    "sadness"
  ],
  "emotion_label": "anxiety",
  "valence_score": -0.21,
  "energy_score": 0.54,
  "stress_score": 0.51,
  "confidence": 0.35,
  "provider_name": "en_canonical_emotion+heuristic_fallback",
  "response_mode": "validating_gentle"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "From what you shared, the clearest part is this: feeling left out can land in a quiet but heavy way. It makes sense that this would leave you feeling a bit far from everyone.",
  "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have much energy for more.",
  "safety_note": null,
  "provider_name": "template_fallback"
}
```

**Debug snapshot**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "I keep feeling left out lately, like everyone already has their people.",
    "language": "en",
    "primary_emotion": "anxiety",
    "secondary_emotions": [
      "neutral",
      "sadness"
    ],
    "confidence": 0.35,
    "response_mode": "validating_gentle",
    "topic_tags": [
      "loneliness",
      "daily life"
    ],
    "risk_level": "low",
    "utterance_type": "reflective_checkin",
    "event_type": "loneliness_or_disconnection",
    "relationship_target": null,
    "short_event_flag": false,
    "low_confidence_flag": true,
    "evidence_spans": [
      "left out"
    ],
    "social_context": "loneliness",
    "concern_target": null,
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

## Recognition / praise

**Input**: A friend told me I'd actually be good at helping people solve problems.

**Emotion provider path used**: `en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment`
**Support provider used**: `template_fallback`

**Structured emotion output**

```json
{
  "primary_emotion": "gratitude",
  "secondary_emotions": [
    "joy",
    "neutral"
  ],
  "emotion_label": "grateful",
  "valence_score": 0.42,
  "energy_score": 0.46,
  "stress_score": 0.24,
  "confidence": 0.56,
  "provider_name": "en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment",
  "response_mode": "supportive_reflective"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "Hearing that from someone you know can land in a real way. It makes sense if you are still taking in what those words meant to you.",
  "gentle_suggestion": "If you want, keep the exact line that felt most real.",
  "safety_note": null,
  "provider_name": "template_fallback"
}
```

**Debug snapshot**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "A friend told me I'd actually be good at helping people solve problems.",
    "language": "en",
    "primary_emotion": "gratitude",
    "secondary_emotions": [
      "joy",
      "neutral"
    ],
    "confidence": 0.56,
    "response_mode": "supportive_reflective",
    "topic_tags": [
      "friendship",
      "friends"
    ],
    "risk_level": "low",
    "utterance_type": "appreciation_or_recognition",
    "event_type": "recognition_or_praise",
    "relationship_target": "friend",
    "short_event_flag": false,
    "low_confidence_flag": false,
    "evidence_spans": [
      "friend",
      "told me i'd actually be good",
      "good at helping"
    ],
    "social_context": "friendship",
    "concern_target": "friend",
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

## Responsibility / tension

**Input**: I let my teammate down and I keep replaying it.

**Emotion provider path used**: `en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment`
**Support provider used**: `template_fallback`

**Structured emotion output**

```json
{
  "primary_emotion": "overwhelm",
  "secondary_emotions": [
    "anxiety",
    "sadness"
  ],
  "emotion_label": "strained",
  "valence_score": -0.38,
  "energy_score": 0.5,
  "stress_score": 0.56,
  "confidence": 0.52,
  "provider_name": "en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment",
  "response_mode": "validating_gentle"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "It makes sense that this is sitting heavily after feeling like you let someone down. That kind of tension can linger even when the moment itself is over.",
  "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
  "safety_note": null,
  "provider_name": "template_fallback"
}
```

**Debug snapshot**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "I let my teammate down and I keep replaying it.",
    "language": "en",
    "primary_emotion": "overwhelm",
    "secondary_emotions": [
      "anxiety",
      "sadness"
    ],
    "confidence": 0.52,
    "response_mode": "validating_gentle",
    "topic_tags": [
      "work/school",
      "daily life"
    ],
    "risk_level": "low",
    "utterance_type": "responsibility_tension",
    "event_type": "conflict_or_disappointment",
    "relationship_target": null,
    "short_event_flag": false,
    "low_confidence_flag": false,
    "evidence_spans": [
      "let ... down"
    ],
    "social_context": "work/school",
    "concern_target": null,
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

## Low energy / emotionally flat

**Input**: I feel weirdly empty today.

**Emotion provider path used**: `heuristic_fallback+en_demo_render_adjustment`
**Support provider used**: `template_fallback`

**Structured emotion output**

```json
{
  "primary_emotion": "sadness",
  "secondary_emotions": [],
  "emotion_label": "nặng nề",
  "valence_score": -0.56,
  "energy_score": 0.22,
  "stress_score": 0.36,
  "confidence": 0.35,
  "provider_name": "heuristic_fallback+en_demo_render_adjustment",
  "response_mode": "low_energy_comfort"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "From what you shared, the clearest part is this: being this tired can flatten everything a little. You do not need to force meaning or momentum out of a low-energy day.",
  "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
  "safety_note": null,
  "provider_name": "template_fallback"
}
```

**Debug snapshot**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "I feel weirdly empty today.",
    "language": "en",
    "primary_emotion": "sadness",
    "secondary_emotions": [],
    "confidence": 0.35,
    "response_mode": "low_energy_comfort",
    "topic_tags": [
      "daily life"
    ],
    "risk_level": "low",
    "utterance_type": "low_energy_update",
    "event_type": "exhaustion_or_flatness",
    "relationship_target": null,
    "short_event_flag": false,
    "low_confidence_flag": true,
    "evidence_spans": [
      "empty",
      "weirdly",
      "i feel"
    ],
    "social_context": "daily_life",
    "concern_target": null,
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

## Regression Before/After

### Deadline stress

**Input**: I've had deadlines piling up for days.

**Before note**: Representative pre-redesign output from the old abstract English renderer style.

**Before**

```json
{
  "support": {
    "provider_name": "template_fallback",
    "empathetic_response": "There is a lot of strain here around work. It sounds like part of you is still trying to stay steady."
  },
  "note": "Representative pre-redesign output from the old abstract English renderer style."
}
```

**After**

```json
{
  "input_text": "I've had deadlines piling up for days.",
  "language": "en",
  "topic_tags": [
    "work/school"
  ],
  "risk_level": "low",
  "risk_flags": [],
  "emotion": {
    "primary_emotion": "overwhelm",
    "secondary_emotions": [],
    "emotion_label": "căng",
    "valence_score": -0.5,
    "energy_score": 0.82,
    "stress_score": 0.88,
    "confidence": 0.35,
    "provider_name": "heuristic_fallback",
    "response_mode": "grounding_soft"
  },
  "support": {
    "empathetic_response": "From what you shared, the clearest part is this: having deadlines pile up for days can make everything feel tight and crowded. You do not have to pretend it is manageable for it to count as a lot.",
    "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
    "safety_note": null,
    "provider_name": "template_fallback"
  }
}
```

**After debug**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "I've had deadlines piling up for days.",
    "language": "en",
    "primary_emotion": "overwhelm",
    "secondary_emotions": [],
    "confidence": 0.35,
    "response_mode": "grounding_soft",
    "topic_tags": [
      "work/school"
    ],
    "risk_level": "low",
    "utterance_type": "reflective_checkin",
    "event_type": "deadline_pressure",
    "relationship_target": null,
    "short_event_flag": false,
    "low_confidence_flag": true,
    "evidence_spans": [
      "deadline",
      "deadlines",
      "piling up"
    ],
    "social_context": "work_or_school",
    "concern_target": null,
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

### Loved one sick

**Input**: My girlfriend is sick

**Before note**: Captured pre-fix failure mode from the English demo path.

**Before**

```json
{
  "support": {
    "provider_name": "template_fallback",
    "empathetic_response": "Your energy sounds really low around relationships. I want to acknowledge that tiredness without pushing you to feel different right away."
  },
  "note": "Captured pre-fix failure mode from the English demo path."
}
```

**After**

```json
{
  "input_text": "My girlfriend is sick",
  "language": "en",
  "topic_tags": [
    "relationships",
    "friends",
    "health"
  ],
  "risk_level": "low",
  "risk_flags": [],
  "emotion": {
    "primary_emotion": "anxiety",
    "secondary_emotions": [
      "sadness",
      "neutral"
    ],
    "emotion_label": "concerned",
    "valence_score": -0.24,
    "energy_score": 0.34,
    "stress_score": 0.44,
    "confidence": 0.44,
    "provider_name": "en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment",
    "response_mode": "supportive_reflective"
  },
  "support": {
    "empathetic_response": "Even from a short update like \"My girlfriend is sick\", it makes sense that something emotionally important is sitting underneath. When your girlfriend is unwell, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to them.",
    "gentle_suggestion": "If it helps, pick one small check-in or one practical thing you can do and let that be enough for now.",
    "safety_note": null,
    "provider_name": "template_fallback"
  }
}
```

**After debug**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "My girlfriend is sick",
    "language": "en",
    "primary_emotion": "anxiety",
    "secondary_emotions": [
      "sadness",
      "neutral"
    ],
    "confidence": 0.44,
    "response_mode": "supportive_reflective",
    "topic_tags": [
      "relationships",
      "friends",
      "health"
    ],
    "risk_level": "low",
    "utterance_type": "relationship_concern",
    "event_type": "loved_one_unwell",
    "relationship_target": "girlfriend",
    "short_event_flag": true,
    "low_confidence_flag": true,
    "evidence_spans": [
      "girlfriend",
      "sick"
    ],
    "social_context": "romantic_relationship",
    "concern_target": "girlfriend",
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

### Loneliness

**Input**: I keep feeling left out lately, like everyone already has their people.

**Before note**: Representative pre-redesign loneliness output with generic abstraction.

**Before**

```json
{
  "support": {
    "provider_name": "template",
    "empathetic_response": "There are a few emotional layers moving together here around daily life. Nothing about that needs to be cleaned up too quickly."
  },
  "note": "Representative pre-redesign loneliness output with generic abstraction."
}
```

**After**

```json
{
  "input_text": "I keep feeling left out lately, like everyone already has their people.",
  "language": "en",
  "topic_tags": [
    "loneliness",
    "daily life"
  ],
  "risk_level": "low",
  "risk_flags": [],
  "emotion": {
    "primary_emotion": "anxiety",
    "secondary_emotions": [
      "neutral",
      "sadness"
    ],
    "emotion_label": "anxiety",
    "valence_score": -0.21,
    "energy_score": 0.54,
    "stress_score": 0.51,
    "confidence": 0.35,
    "provider_name": "en_canonical_emotion+heuristic_fallback",
    "response_mode": "validating_gentle"
  },
  "support": {
    "empathetic_response": "From what you shared, the clearest part is this: feeling left out can land in a quiet but heavy way. It makes sense that this would leave you feeling a bit far from everyone.",
    "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have much energy for more.",
    "safety_note": null,
    "provider_name": "template_fallback"
  }
}
```

**After debug**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "I keep feeling left out lately, like everyone already has their people.",
    "language": "en",
    "primary_emotion": "anxiety",
    "secondary_emotions": [
      "neutral",
      "sadness"
    ],
    "confidence": 0.35,
    "response_mode": "validating_gentle",
    "topic_tags": [
      "loneliness",
      "daily life"
    ],
    "risk_level": "low",
    "utterance_type": "reflective_checkin",
    "event_type": "loneliness_or_disconnection",
    "relationship_target": null,
    "short_event_flag": false,
    "low_confidence_flag": true,
    "evidence_spans": [
      "left out"
    ],
    "social_context": "solo",
    "concern_target": null,
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

### Recognition / praise

**Input**: A friend told me I'd actually be good at helping people solve problems.

**Before note**: Representative pre-fix output before recognition-specific rendering was added.

**Before**

```json
{
  "support": {
    "provider_name": "template",
    "empathetic_response": "There is a real thread of worry here around friends. At the same time, it sounds like part of you is still trying to stay steady."
  },
  "note": "Representative pre-fix output before recognition-specific rendering was added."
}
```

**After**

```json
{
  "input_text": "A friend told me I'd actually be good at helping people solve problems.",
  "language": "en",
  "topic_tags": [
    "friends"
  ],
  "risk_level": "low",
  "risk_flags": [],
  "emotion": {
    "primary_emotion": "gratitude",
    "secondary_emotions": [
      "joy",
      "neutral"
    ],
    "emotion_label": "grateful",
    "valence_score": 0.42,
    "energy_score": 0.46,
    "stress_score": 0.24,
    "confidence": 0.56,
    "provider_name": "en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment",
    "response_mode": "supportive_reflective"
  },
  "support": {
    "empathetic_response": "Hearing that from someone you know can land in a real way. It makes sense if you are still taking in what those words meant to you.",
    "gentle_suggestion": "If you want, keep the exact line that felt most real.",
    "safety_note": null,
    "provider_name": "template_fallback"
  }
}
```

**After debug**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "A friend told me I'd actually be good at helping people solve problems.",
    "language": "en",
    "primary_emotion": "gratitude",
    "secondary_emotions": [
      "joy",
      "neutral"
    ],
    "confidence": 0.56,
    "response_mode": "supportive_reflective",
    "topic_tags": [
      "friends"
    ],
    "risk_level": "low",
    "utterance_type": "appreciation_or_recognition",
    "event_type": "recognition_or_praise",
    "relationship_target": "friend",
    "short_event_flag": false,
    "low_confidence_flag": false,
    "evidence_spans": [
      "friend",
      "told me i'd actually be good",
      "good at helping"
    ],
    "social_context": "friendship",
    "concern_target": "friend",
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

### Responsibility / tension

**Input**: I let my teammate down and I keep replaying it.

**Before note**: Representative pre-redesign output that missed the responsibility tension event.

**Before**

```json
{
  "support": {
    "provider_name": "template",
    "empathetic_response": "There is a lot of strain in what you described around work. That reaction makes sense and does not need to be dismissed."
  },
  "note": "Representative pre-redesign output that missed the responsibility tension event."
}
```

**After**

```json
{
  "input_text": "I let my teammate down and I keep replaying it.",
  "language": "en",
  "topic_tags": [
    "daily life"
  ],
  "risk_level": "low",
  "risk_flags": [],
  "emotion": {
    "primary_emotion": "overwhelm",
    "secondary_emotions": [
      "anxiety",
      "sadness"
    ],
    "emotion_label": "strained",
    "valence_score": -0.38,
    "energy_score": 0.5,
    "stress_score": 0.56,
    "confidence": 0.52,
    "provider_name": "en_canonical_emotion+heuristic_fallback+en_demo_render_adjustment",
    "response_mode": "validating_gentle"
  },
  "support": {
    "empathetic_response": "It makes sense that this is sitting heavily after feeling like you let someone down. That kind of tension can linger even when the moment itself is over.",
    "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
    "safety_note": null,
    "provider_name": "template_fallback"
  }
}
```

**After debug**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "I let my teammate down and I keep replaying it.",
    "language": "en",
    "primary_emotion": "overwhelm",
    "secondary_emotions": [
      "anxiety",
      "sadness"
    ],
    "confidence": 0.52,
    "response_mode": "validating_gentle",
    "topic_tags": [
      "daily life"
    ],
    "risk_level": "low",
    "utterance_type": "responsibility_tension",
    "event_type": "conflict_or_disappointment",
    "relationship_target": null,
    "short_event_flag": false,
    "low_confidence_flag": false,
    "evidence_spans": [
      "let ... down"
    ],
    "social_context": "solo",
    "concern_target": null,
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```

### Low-energy update

**Input**: I feel weirdly empty today.

**Before note**: Representative pre-redesign low-energy output with generic copy.

**Before**

```json
{
  "support": {
    "provider_name": "template",
    "empathetic_response": "Your energy sounds really low around daily life. I want to acknowledge that tiredness without pushing you to feel different right away."
  },
  "note": "Representative pre-redesign low-energy output with generic copy."
}
```

**After**

```json
{
  "input_text": "I feel weirdly empty today.",
  "language": "en",
  "topic_tags": [
    "daily life"
  ],
  "risk_level": "low",
  "risk_flags": [],
  "emotion": {
    "primary_emotion": "sadness",
    "secondary_emotions": [],
    "emotion_label": "nặng nề",
    "valence_score": -0.56,
    "energy_score": 0.22,
    "stress_score": 0.36,
    "confidence": 0.35,
    "provider_name": "heuristic_fallback+en_demo_render_adjustment",
    "response_mode": "low_energy_comfort"
  },
  "support": {
    "empathetic_response": "From what you shared, the clearest part is this: being this tired can flatten everything a little. You do not need to force meaning or momentum out of a low-energy day.",
    "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
    "safety_note": null,
    "provider_name": "template_fallback"
  }
}
```

**After debug**

```json
{
  "renderer_selected": "template_fallback",
  "fallback_triggered": true,
  "fallback_reason": "Response provider 'gemini' requires GEMINI_API_KEY",
  "render_payload": {
    "input_text": "I feel weirdly empty today.",
    "language": "en",
    "primary_emotion": "sadness",
    "secondary_emotions": [],
    "confidence": 0.35,
    "response_mode": "low_energy_comfort",
    "topic_tags": [
      "daily life"
    ],
    "risk_level": "low",
    "utterance_type": "low_energy_update",
    "event_type": "exhaustion_or_flatness",
    "relationship_target": null,
    "short_event_flag": false,
    "low_confidence_flag": true,
    "evidence_spans": [
      "empty",
      "weirdly",
      "i feel"
    ],
    "social_context": "solo",
    "concern_target": null,
    "suggestion_allowed": true
  },
  "system_instruction": "ROLE: You are a warm, emotionally aware wellness companion. You are not a therapist, not a clinician, not a coach, and not a diagnosis engine.\nPRIMARY OBJECTIVE: Write a short supportive response that helps the user feel heard, understood, and gently supported.\nRESPONSE PRINCIPLES:\n- Acknowledge the user's feeling or situation first.\n- Ground the response in the actual event or wording from the user's text.\n- If the input is short and factual, respond to the event directly before reflecting inner emotion.\n- If another person matters in the situation, acknowledge relational concern first.\n- Be non-judgmental and emotionally validating without exaggerating.\n- If confidence is low, be tentative but still specific.\n- Offer at most one light, optional suggestion only if it fits naturally.\n- Keep the response short, warm, and human.\nSTYLE CONSTRAINTS:\n- natural English\n- emotionally specific but not overblown\n- no clinical tone\n- no therapist tone\n- no motivational-poster tone\n- no abstract category phrases like 'around relationships', 'around work', or 'around daily life'\n- no vague meta openers like 'I may not be catching every layer of this', 'It sounds like part of you', or 'There is a thread of'\n- do not over-interpret beyond the evidence in the text and payload",
  "few_shots": [
    {
      "render_payload": {
        "input_text": "I've had deadlines piling up for days.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety"
        ],
        "confidence": 0.77,
        "response_mode": "grounding_soft",
        "topic_tags": [
          "work/school"
        ],
        "risk_level": "low",
        "utterance_type": "distress_checkin",
        "event_type": "deadline_pressure",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "deadlines",
          "piling up"
        ],
        "social_context": "work_or_school",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Having deadlines pile up for days can make everything feel tight and crowded. You do not have to downplay that just to keep going.",
        "gentle_suggestion": "If it helps, choose the next smallest thing instead of the whole pile.",
        "safety_note": null,
        "style": "grounding_soft",
        "specificity": "high",
        "reasoning_note": "Event-first response for deadline pressure with one light next step."
      }
    },
    {
      "render_payload": {
        "input_text": "My girlfriend is sick",
        "language": "en",
        "primary_emotion": "anxiety",
        "secondary_emotions": [
          "sadness",
          "neutral"
        ],
        "confidence": 0.48,
        "response_mode": "supportive_reflective",
        "topic_tags": [
          "relationships",
          "health"
        ],
        "risk_level": "low",
        "utterance_type": "relationship_concern",
        "event_type": "loved_one_unwell",
        "relationship_target": "girlfriend",
        "short_event_flag": true,
        "low_confidence_flag": true,
        "evidence_spans": [
          "girlfriend",
          "sick"
        ],
        "social_context": "romantic_relationship",
        "concern_target": "girlfriend",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "When your girlfriend is sick, even a short update can carry a lot of worry. It makes sense if part of your attention keeps circling back to her.",
        "gentle_suggestion": "If it helps, one small check-in or one practical act of care is enough for now.",
        "safety_note": null,
        "style": "supportive_reflective",
        "specificity": "high",
        "reasoning_note": "Relational concern first, grounded in the event, cautious because confidence is modest."
      }
    },
    {
      "render_payload": {
        "input_text": "I feel weirdly empty today.",
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": [
          "neutral"
        ],
        "confidence": 0.61,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "daily life"
        ],
        "risk_level": "low",
        "utterance_type": "low_energy_update",
        "event_type": "exhaustion_or_flatness",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "empty"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "That kind of emptiness can make a day feel quietly hard to move through. You do not have to force a cleaner explanation for it right away.",
        "gentle_suggestion": "If it helps, let the next thing be small and easy on purpose.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "medium",
        "reasoning_note": "Soft comfort for flatness without abstract language or over-interpretation."
      }
    },
    {
      "render_payload": {
        "input_text": "A friend told me I'd actually be good at helping people solve problems.",
        "language": "en",
        "primary_emotion": "gratitude",
        "secondary_emotions": [
          "joy",
          "neutral"
        ],
        "confidence": 0.66,
        "response_mode": "celebratory_warm",
        "topic_tags": [
          "friendship",
          "recognition"
        ],
        "risk_level": "low",
        "utterance_type": "appreciation_or_recognition",
        "event_type": "recognition_or_praise",
        "relationship_target": "friend",
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "friend",
          "good at helping people solve problems"
        ],
        "social_context": "friendship",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Hearing that from a friend can land in a real way. It makes sense if those words are still sitting with you.",
        "gentle_suggestion": "If you want, hold onto the exact part that felt most believable.",
        "safety_note": null,
        "style": "celebratory_warm",
        "specificity": "high",
        "reasoning_note": "Warm recognition response, not anxiety-coded."
      }
    },
    {
      "render_payload": {
        "input_text": "I keep feeling left out lately, like everyone already has their people.",
        "language": "en",
        "primary_emotion": "loneliness",
        "secondary_emotions": [
          "sadness"
        ],
        "confidence": 0.73,
        "response_mode": "low_energy_comfort",
        "topic_tags": [
          "loneliness"
        ],
        "risk_level": "low",
        "utterance_type": "reflective_checkin",
        "event_type": "loneliness_or_disconnection",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "left out",
          "everyone already has their people"
        ],
        "social_context": "solo",
        "concern_target": null,
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "Feeling left out can hit in a quiet but heavy way. It makes sense that this would leave you feeling a little far from everyone.",
        "gentle_suggestion": "If it helps, one small reach-out still counts even if you do not have energy for more.",
        "safety_note": null,
        "style": "low_energy_comfort",
        "specificity": "high",
        "reasoning_note": "Grounded loneliness response with light optional connection."
      }
    },
    {
      "render_payload": {
        "input_text": "I let my teammate down and I keep replaying it.",
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": [
          "anxiety",
          "sadness"
        ],
        "confidence": 0.68,
        "response_mode": "validating_gentle",
        "topic_tags": [
          "work/school",
          "relationships"
        ],
        "risk_level": "low",
        "utterance_type": "responsibility_tension",
        "event_type": "conflict_or_disappointment",
        "relationship_target": null,
        "short_event_flag": false,
        "low_confidence_flag": false,
        "evidence_spans": [
          "let my teammate down",
          "keep replaying it"
        ],
        "social_context": "work_or_school",
        "concern_target": "teammate",
        "suggestion_allowed": true
      },
      "output": {
        "empathetic_response": "It makes sense that this is sticking with you after feeling like you let someone down. That kind of tension can stay loud even after the moment itself is over.",
        "gentle_suggestion": "If it helps, one honest next step is enough for tonight.",
        "safety_note": null,
        "style": "validating_gentle",
        "specificity": "high",
        "reasoning_note": "Responsibility tension response without blame or therapy tone."
      }
    }
  ],
  "raw_renderer_output": null
}
```
