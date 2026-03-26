# Backend Response Quality Evals

This is a lightweight regression workflow for companion response quality. It uses the real backend response pipeline, writes readable artifacts, and stays small enough to review in normal code changes.

## What It Includes

- `response_quality_cases.json`
  - Curated prompt set covering greetings, neutral check-ins, sadness, overload, guilt, relief, other-person concern, ambiguous ownership, deadline pressure, low energy, frustration, and mixed recovery.
- `backend/scripts/evaluate_response_quality.py`
  - Runner that executes the current backend pipeline on the case set and writes review artifacts.

## How To Run

Use the backend venv and point `PYTHONPATH` at `backend`:

```bash
env PYTHONPATH=backend backend/.venv/bin/python backend/scripts/evaluate_response_quality.py
```

Useful options:

```bash
env PYTHONPATH=backend backend/.venv/bin/python backend/scripts/evaluate_response_quality.py --provider mock
env PYTHONPATH=backend backend/.venv/bin/python backend/scripts/evaluate_response_quality.py --category other_person_concern
env PYTHONPATH=backend backend/.venv/bin/python backend/scripts/evaluate_response_quality.py --case-id other-01
env PYTHONPATH=backend backend/.venv/bin/python backend/scripts/evaluate_response_quality.py --baseline backend/evals/results/<old-run>/results.json
```

By default the runner uses the currently configured response provider. Use `--provider mock` for a stable local smoke pass, or leave it unset to evaluate the live configured backend response path.

## Output Artifacts

Each run writes to `backend/evals/results/<run-name>/`:

- `results.json`
  - Full structured output, including per-case context, response text, and heuristic flags.
- `responses.jsonl`
  - One row per case for quick diffs and tooling.
- `review_template.csv`
  - Manual scoring sheet with blank rubric columns.
- `report.md`
  - Quick review summary with repeated phrasing counts, flagged cases, and optional baseline diffs.

## Manual Scoring Rubric

Score each row in `review_template.csv` with:

- `naturalness_1_5`
  - Does this sound like a thoughtful human companion?
- `groundedness_1_5`
  - Is the response evidence-bounded and free of unsupported narrative leaps?
- `non_redundancy_1_5`
  - Does it avoid saying the same thing multiple ways?
- `self_vs_other_correctness_1_5_or_na`
  - For other-person concern cases, does it center the user's concern rather than mis-assign ownership?
- `brevity_discipline_1_5`
  - Is the response concise and controlled?
- `follow_up_usefulness_1_5_or_na`
  - If there is a question, is it natural and worth asking?
- `anti_template_feel_1_5`
  - Does it avoid canned or therapy-like phrasing?

Suggested interpretation:

- `5`: strong
- `4`: good
- `3`: acceptable but noticeable issues
- `2`: weak
- `1`: poor / obvious regression

## Lightweight Heuristics

The runner adds cheap regression flags. These are not quality truth, but they help catch drift:

- response too long for the case
- unexpected or missing follow-up question
- more than one question in a single reply
- too many sentences
- high overlap between empathy, suggestion, and question
- repeated opening stems across many outputs
- repeated question stems across many outputs
- stock phrase hits such as:
  - `It sounds like`
  - `You're really noticing`
  - `What feels most present`
  - `as you sit with this`
- self-vs-other owner drift in other-person concern cases

## Reviewing Changes Over Time

Recommended loop:

1. Run the eval before a response-quality change and keep the `results.json`.
2. Run it again after the change.
3. Use `--baseline` to generate a markdown diff summary.
4. Manually score the highest-risk categories:
   - `other_person_concern`
   - `greeting_opening`
   - `positive_relief_gratitude`
   - `self_stress_overload`
5. Spot-check any flagged repeated openings or overlap-heavy cases in `report.md`.

This is intentionally a small workflow. The goal is to make response regressions obvious without building a heavyweight benchmark framework.
