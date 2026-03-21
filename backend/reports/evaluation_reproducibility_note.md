# Evaluation Reproducibility Note

Current benchmark reports in this repository should be treated as snapshots, not live truth.

## Known Caveats

- `benchmarks/reports/ai_core_eval_report.md` evaluates a VI/ZH dataset and is not directly comparable to the newer English-first demo path.
- canonical-model evaluation and demo reports may have been generated from different model artifacts and different points in the code history.
- no benchmark numbers in this note are newly generated.

## Re-run Commands

From `backend/` after installing dependencies:

```bash
python -m benchmarks.evaluate_ai_core
python -m benchmarks.evaluate_canonical_models
python -m scripts.smoke_test_ai_core
```

## What To Capture When Re-running

- current commit SHA
- active `.env` or config preset
- which model artifacts exist under `backend/models/`
- whether Hugging Face runtime was online or offline
- output reports written under `backend/benchmarks/reports/` and `backend/reports/`

## Recommendation

Before publishing benchmark claims, regenerate all evaluation reports from one clean environment after the shared pipeline refactor lands and record the exact config used for each run.
