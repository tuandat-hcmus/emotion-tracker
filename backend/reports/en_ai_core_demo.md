# English AI Core Demo

Generated from the live English-first AI core demo service path.

## Work stress / deadline

**Input**: I have been carrying too many deadlines at once, and my brain has felt packed tight all day.

**Emotion provider path used**: `en_canonical_emotion`
**Support provider used**: `template`

**Structured emotion output**

```json
{
  "primary_emotion": "overwhelm",
  "secondary_emotions": [
    "anger",
    "anxiety"
  ],
  "emotion_label": "overwhelm",
  "valence_score": -0.46,
  "energy_score": 0.79,
  "stress_score": 0.83,
  "confidence": 0.86,
  "provider_name": "en_canonical_emotion",
  "response_mode": "grounding_soft"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "The pressure sounds pretty intense around work/school. You do not need to force yourself to feel okay right away for this to count as a hard moment.",
  "gentle_suggestion": "If it helps, let your shoulders drop and exhale a little more slowly once.",
  "safety_note": null,
  "provider_name": "template"
}
```

## Loneliness / left behind

**Input**: I keep seeing everyone move forward with their lives, and I feel strangely left behind and hard to reach.

**Emotion provider path used**: `en_canonical_emotion+heuristic_fallback`
**Support provider used**: `template`

**Structured emotion output**

```json
{
  "primary_emotion": "sadness",
  "secondary_emotions": [
    "neutral",
    "joy"
  ],
  "emotion_label": "sadness",
  "valence_score": -0.19,
  "energy_score": 0.44,
  "stress_score": 0.41,
  "confidence": 0.35,
  "provider_name": "en_canonical_emotion+heuristic_fallback",
  "response_mode": "supportive_reflective"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "I may not be reading every part of this perfectly. I may not be catching every layer of this, but right now there are a few emotional layers moving together here around loneliness. Nothing about that needs to be cleaned up too quickly.",
  "gentle_suggestion": "If you want, name the heaviest part first and leave the rest for later.",
  "safety_note": null,
  "provider_name": "template"
}
```

## Relief / gratitude

**Input**: A small kindness landed at exactly the right moment today, and I feel genuinely grateful for it.

**Emotion provider path used**: `en_canonical_emotion+en_demo_utterance_adjustment`
**Support provider used**: `template`

**Structured emotion output**

```json
{
  "primary_emotion": "gratitude",
  "secondary_emotions": [
    "joy",
    "neutral"
  ],
  "emotion_label": "gratitude",
  "valence_score": 0.38,
  "energy_score": 0.46,
  "stress_score": 0.12,
  "confidence": 0.94,
  "provider_name": "en_canonical_emotion+en_demo_utterance_adjustment",
  "response_mode": "celebratory_warm"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "That kind of recognition can land more deeply than people expect around gratitude/achievement. It makes sense if part of you is still taking in what it means.",
  "gentle_suggestion": "If you want, hold onto the exact words that felt most believable.",
  "safety_note": null,
  "provider_name": "template"
}
```

## Low energy / exhausted mood

**Input**: I am not intensely sad, just deeply tired and low on battery. Everything feels slower than it should.

**Emotion provider path used**: `en_canonical_emotion+heuristic_fallback`
**Support provider used**: `template`

**Structured emotion output**

```json
{
  "primary_emotion": "sadness",
  "secondary_emotions": [
    "neutral",
    "loneliness"
  ],
  "emotion_label": "sadness",
  "valence_score": -0.14,
  "energy_score": 0.36,
  "stress_score": 0.34,
  "confidence": 0.66,
  "provider_name": "en_canonical_emotion+heuristic_fallback",
  "response_mode": "low_energy_comfort"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "From what you're sharing, it seems like your energy sounds really low around health. I want to acknowledge that tiredness without pushing you to snap out of it.",
  "gentle_suggestion": "If you can, give yourself one very small pause without asking anything else from yourself.",
  "safety_note": null,
  "provider_name": "template"
}
```

## Mixed emotion / nervous but hopeful

**Input**: I start something new tomorrow, so I feel nervous and hopeful at the same time.

**Emotion provider path used**: `en_canonical_emotion+heuristic_fallback`
**Support provider used**: `template`

**Structured emotion output**

```json
{
  "primary_emotion": "overwhelm",
  "secondary_emotions": [
    "anger",
    "anxiety"
  ],
  "emotion_label": "overwhelm",
  "valence_score": -0.36,
  "energy_score": 0.68,
  "stress_score": 0.67,
  "confidence": 0.35,
  "provider_name": "en_canonical_emotion+heuristic_fallback",
  "response_mode": "grounding_soft"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "I may not be reading every part of this perfectly. I may not be catching every layer of this, but right now the pressure sounds pretty intense around daily life. You do not need to force yourself to feel okay right away for this to count as a hard moment.",
  "gentle_suggestion": "If it helps, let your shoulders drop and exhale a little more slowly once.",
  "safety_note": null,
  "provider_name": "template"
}
```

## Regression Before/After

### Relationship concern / short health update

**Input**: My girlfriend is sick

**Before note**: Captured pre-fix failure mode from the English demo path.

**Before**

```json
{
  "emotion": {
    "primary_emotion": "sadness",
    "response_mode": "low_energy_comfort",
    "provider_name": "visolex/phobert-emotion"
  },
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
    "emotion_label": "anxiety",
    "valence_score": -0.24,
    "energy_score": 0.36,
    "stress_score": 0.44,
    "confidence": 0.35,
    "provider_name": "en_canonical_emotion+heuristic_fallback+en_demo_utterance_adjustment",
    "response_mode": "supportive_reflective"
  },
  "support": {
    "empathetic_response": "I may not be catching every layer of this, but right now it makes sense that your attention is going to your girlfriend first. When someone you care about is unwell, even a short update can leave a lot of concern sitting in the background.",
    "gentle_suggestion": "If it helps, one small check-in or one practical act of care may feel steadier than looping alone.",
    "safety_note": null,
    "provider_name": "template"
  }
}
```

### Recognition / appreciation

**Input**: A friend told me I'd actually be good at helping people solve problems.

**Before note**: Representative pre-fix output before the appreciation utterance-type rule was added.

**Before**

```json
{
  "emotion": {
    "primary_emotion": "anxiety",
    "response_mode": "supportive_reflective",
    "provider_name": "en_canonical_emotion+heuristic_fallback"
  },
  "support": {
    "provider_name": "template",
    "empathetic_response": "There is a real thread of worry here around friends. At the same time, it sounds like part of you is still trying to stay steady."
  },
  "note": "Representative pre-fix output before the appreciation utterance-type rule was added."
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
    "emotion_label": "gratitude",
    "valence_score": 0.38,
    "energy_score": 0.46,
    "stress_score": 0.28,
    "confidence": 0.52,
    "provider_name": "en_canonical_emotion+heuristic_fallback+en_demo_utterance_adjustment",
    "response_mode": "supportive_reflective"
  },
  "support": {
    "empathetic_response": "From what you're sharing, it seems like that kind of recognition can land more deeply than people expect around friends. It makes sense if part of you is still taking in what it means.",
    "gentle_suggestion": "If you want, hold onto the exact words that felt most believable.",
    "safety_note": null,
    "provider_name": "template"
  }
}
```
