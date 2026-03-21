# Hugging Face emotion baseline

This repo now includes a first end-to-end Hugging Face training pipeline for English multi-label emotion classification on `go_emotions`.

## Default choices

- Dataset: `go_emotions` with config `raw`
- Default CPU/smoke backbone: `distilroberta-base`
- Default larger backbone for non-smoke use: `roberta-base`
- Training objective: multi-label classification over the raw GoEmotions label set

The CPU default is intentionally practical for local smoke training. Use `--model-name roberta-base` for a stronger baseline once you want a fuller run.

## Smoke training

Run from repo root:

```bash
PYTHONPATH=backend USE_TF=0 USE_FLAX=0 \
  backend/.venv/bin/python backend/training/train_hf_emotion_baseline.py \
  --output-dir backend/models/en_goemotions_baseline_smoke \
  --smoke \
  --epochs 1 \
  --train-batch-size 4 \
  --eval-batch-size 4 \
  --max-length 128
```

Smoke mode limits the dataset to small fixed splits. It now uses CUDA automatically when available unless you pass `--cpu-only`.

## Larger training run

```bash
PYTHONPATH=backend USE_TF=0 USE_FLAX=0 \
  backend/.venv/bin/python backend/training/train_hf_emotion_baseline.py \
  --output-dir backend/models/en_goemotions_baseline_v1 \
  --model-name roberta-base \
  --epochs 2 \
  --train-batch-size 8 \
  --eval-batch-size 8 \
  --max-length 128 \
  --learning-rate 2e-5
```

## GPU-ready run for RTX 3060

```bash
PYTHONPATH=backend USE_TF=0 USE_FLAX=0 \
  backend/.venv/bin/python backend/training/train_hf_emotion_baseline.py \
  --output-dir backend/models/en_goemotions_baseline_distil_gpu_v1 \
  --model-name distilroberta-base \
  --epochs 2 \
  --train-batch-size 16 \
  --eval-batch-size 16 \
  --max-length 128 \
  --train-limit 2048 \
  --validation-limit 256 \
  --test-limit 256
```

The trainer will select `cuda` automatically when `torch.cuda.is_available()` is true. Use `--cpu-only` to force CPU.

## Evaluation

```bash
PYTHONPATH=backend USE_TF=0 USE_FLAX=0 \
  backend/.venv/bin/python backend/training/evaluate_hf_emotion_baseline.py \
  --model-dir backend/models/en_goemotions_baseline_smoke
```

## Inference wrapper

Minimal repo wrapper:

- `backend/app/services/ai_core/hf_emotion_checkpoint_service.py`

Usage pattern:

```python
from app.services.ai_core.hf_emotion_checkpoint_service import predict_checkpoint_emotions

prediction = predict_checkpoint_emotions(
    "I feel relieved but still a bit empty.",
    model_dir="backend/models/en_goemotions_baseline_smoke",
)
```

This returns:

- `top_labels`
- full `probabilities`
- `threshold`
- `model_name`

## Artifacts

Each trained output directory contains:

- Hugging Face model checkpoint
- tokenizer files
- `metrics.json`
- `evaluation_metrics.json` after explicit eval
- `dataset_summary.json`
- `goemotions_baseline_config.json`
