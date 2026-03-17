# Canonical Emotion Annotation Guide

This project uses one product-level canonical emotion schema for wellness check-ins:

- `joy`
- `sadness`
- `anxiety`
- `anger`
- `overwhelm`
- `gratitude`
- `loneliness`
- `neutral`

This is not a diagnostic taxonomy. The label should describe the dominant felt state in a short journaling check-in.

## Label Definitions

`joy`
- Warm positive activation, relief-like lift, hope with clear upward movement, or feeling lighter after strain.
- Includes mild pride or relief when the user is mainly experiencing uplift.

`gratitude`
- Appreciation directed toward a person, support, care, or a stabilizing moment.
- Use when thankfulness is the emotional center, not just a polite phrase.

`sadness`
- Loss, heaviness, disappointment, emptiness, shutdown, emotional flatness with pain, or low-energy hurt.
- Includes depleted states when the main signal is heaviness rather than pressure.

`loneliness`
- Felt disconnection, wanting closeness, feeling unseen, isolated, or emotionally alone.
- Use when the pain is specifically about missing connection.

`anxiety`
- Anticipatory worry, uncertainty, tension, rumination, or low-to-moderate stress with future focus.
- Common in mild check-ins about upcoming tasks, social worry, or “I can’t settle.”

`overwhelm`
- Stress load is the center: too many demands, cognitive flooding, pressure pile-up, “I can’t keep up.”
- Usually higher stress and activation than `anxiety`.

`anger`
- Irritation, frustration, resentment, feeling wronged, or disgust-like rejection.
- Use when friction or protest is the dominant energy.

`neutral`
- No strong dominant emotion, observational update, steady state, or emotionally flat but not clearly painful.
- Can include calm and “just okay” check-ins.

## Boundary Rules

`anxiety` vs `overwhelm`
- `anxiety`: future-oriented worry, uncertainty, bodily tension, waiting for something bad.
- `overwhelm`: demand overload, too many tasks, feeling swamped, compressed, mentally flooded.
- If both appear, choose `overwhelm` when pressure/load is more central than worry.

`sadness` vs `loneliness`
- `sadness`: general heaviness, loss, disappointment, emotional shutdown.
- `loneliness`: the hurt is specifically tied to missing support, closeness, or being unseen.
- If the user says they are sad because nobody is there for them, prefer `loneliness`.

`joy` vs `gratitude`
- `joy`: feeling good, lighter, relieved, encouraged, or happy in a broad sense.
- `gratitude`: appreciation toward support, care, safety, or a helpful person/event.
- If “thankful” is clearly present and emotionally central, prefer `gratitude`.

`neutral` vs emotional suppression
- Use `neutral` only when the text is genuinely low-signal, observational, or emotionally even.
- If the text suggests numbness, shutdown, hollowness, or suppressed pain, prefer `sadness`.

## Valence / Energy / Stress

Assign continuous scores:

- `valence_score`: `-1.0` very negative to `1.0` very positive
- `energy_score`: `0.0` shut down / flat to `1.0` highly activated
- `stress_score`: `0.0` calm / low pressure to `1.0` very strained / overloaded

Guidelines:
- `joy`: positive valence, usually medium-to-high energy, low stress
- `gratitude`: positive valence, low-to-medium energy, low stress
- `sadness`: negative valence, low energy, low-to-medium stress
- `loneliness`: negative valence, low energy, medium stress
- `anxiety`: negative valence, medium-to-high energy, high stress
- `overwhelm`: negative valence, high energy, very high stress
- `anger`: negative valence, high energy, high stress
- `neutral`: near-zero valence, low-to-medium energy, low stress

## Mixed Emotions

Every row must include a `primary_emotion` and may include `secondary_emotions`.

Rules:
- Pick the state that would most influence the support response as `primary_emotion`.
- Keep up to 2 secondary emotions.
- Mixed positive-negative statements should still choose one primary label.
- Example: “I’m relieved but still tense” can be:
  - primary: `joy`
  - secondary: `anxiety`
- Example: “I’m grateful but also exhausted” can be:
  - primary: `gratitude`
  - secondary: `sadness`

## Exclusions

- Do not infer diagnosis.
- Do not annotate suicidality, mania, trauma severity, or clinical syndromes.
- Keep labels grounded in what the user explicitly expresses in a short supportive wellness check-in.
