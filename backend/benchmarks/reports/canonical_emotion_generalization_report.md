# Canonical Emotion Generalization Report

Grouped split policy:
- grouped_hash_by_source_group_70_20_10
- `source_group` is the split boundary. No group appears across train/validation/test.

Selected stack:
```json
{
  "main_language": "en",
  "en_public_model": "SamLowe/roberta-base-go_emotions",
  "vi_public_model": "visolex/phobert-emotion",
  "zh_public_model": "Johnson8187/Chinese-Emotion-Small",
  "multilingual_model": "MilaNLProc/xlm-emo-t",
  "en_canonical_dir": "backend/models/en_canonical_emotion",
  "vi_canonical_dir": "backend/models/vi_canonical_emotion",
  "zh_canonical_dir": "backend/models/zh_canonical_emotion",
  "en_canonical_backbone": "roberta-base",
  "vi_canonical_backbone": "visolex/phobert-emotion",
  "zh_canonical_backbone": "Johnson8187/Chinese-Emotion-Small",
  "ai_confidence_threshold": 0.5,
  "ai_low_confidence_hybrid": true
}
```

Dataset sizes:
- total: 256
- test: 32
- en total: 256

Label distribution:
```json
{
  "anger": 32,
  "anxiety": 32,
  "gratitude": 32,
  "joy": 32,
  "loneliness": 32,
  "neutral": 32,
  "overwhelm": 32,
  "sadness": 32
}
```

Source-group distribution:
```json
{
  "body_exhaustion_v0": 8,
  "body_exhaustion_v1": 8,
  "body_exhaustion_v2": 8,
  "body_exhaustion_v3": 8,
  "family_health_v0": 8,
  "family_health_v1": 8,
  "family_health_v2": 8,
  "family_health_v3": 8,
  "financial_pressure_v0": 8,
  "financial_pressure_v1": 8,
  "financial_pressure_v2": 8,
  "financial_pressure_v3": 8,
  "friend_drift_v0": 8,
  "friend_drift_v1": 8,
  "friend_drift_v2": 8,
  "friend_drift_v3": 8,
  "new_beginning_v0": 8,
  "new_beginning_v1": 8,
  "new_beginning_v2": 8,
  "new_beginning_v3": 8,
  "relationship_distance_v0": 8,
  "relationship_distance_v1": 8,
  "relationship_distance_v2": 8,
  "relationship_distance_v3": 8,
  "self_doubt_v0": 8,
  "self_doubt_v1": 8,
  "self_doubt_v2": 8,
  "self_doubt_v3": 8,
  "work_deadline_v0": 8,
  "work_deadline_v1": 8,
  "work_deadline_v2": 8,
  "work_deadline_v3": 8
}
```

Artifact metadata:
```json
{
  "en_lightweight": {
    "language": "en",
    "backbone_name": "roberta-base",
    "backbone_applied_in_training": false,
    "backbone_runtime_status": "unknown",
    "training_mode": "lightweight_tfidf_head",
    "dataset_name": "realistic",
    "split_policy": "grouped_hash_by_source_group_70_20_10",
    "label_schema_version": "canonical_v1",
    "train_size": 176,
    "validation_size": 48,
    "test_size": 32,
    "label_distribution": {
      "anger": 32,
      "anxiety": 32,
      "gratitude": 32,
      "joy": 32,
      "loneliness": 32,
      "neutral": 32,
      "overwhelm": 32,
      "sadness": 32
    },
    "temperature": 0.7,
    "confidence_threshold": 0.5,
    "training_command": "python -m training.train_canonical_emotion --language en --dataset realistic --mode lightweight",
    "validation_metrics": {
      "accuracy": 1.0,
      "macro_f1": 1.0,
      "coverage_at_threshold": 1.0
    }
  },
  "en_transformer": {
    "language": "en",
    "backbone_name": "roberta-base",
    "backbone_applied_in_training": false,
    "backbone_runtime_status": "unknown",
    "training_mode": "lightweight_tfidf_head",
    "dataset_name": "realistic",
    "split_policy": "grouped_hash_by_source_group_70_20_10",
    "label_schema_version": "canonical_v1",
    "train_size": 176,
    "validation_size": 48,
    "test_size": 32,
    "label_distribution": {
      "anger": 32,
      "anxiety": 32,
      "gratitude": 32,
      "joy": 32,
      "loneliness": 32,
      "neutral": 32,
      "overwhelm": 32,
      "sadness": 32
    },
    "temperature": 0.7,
    "confidence_threshold": 0.5,
    "training_command": "python -m training.train_canonical_emotion --language en --dataset realistic --mode lightweight",
    "validation_metrics": {
      "accuracy": 1.0,
      "macro_f1": 1.0,
      "coverage_at_threshold": 1.0
    }
  },
  "vi_lightweight": {
    "language": "vi",
    "backbone_name": "visolex/phobert-emotion",
    "backbone_applied_in_training": true,
    "backbone_runtime_status": "direct_classifier",
    "training_mode": "lightweight_tfidf_head",
    "dataset_name": "realistic",
    "split_policy": "grouped_hash_by_source_group_70_20_10",
    "label_schema_version": "canonical_v1",
    "train_size": 192,
    "validation_size": 40,
    "test_size": 24,
    "label_distribution": {
      "anger": 32,
      "anxiety": 32,
      "gratitude": 32,
      "joy": 32,
      "loneliness": 32,
      "neutral": 32,
      "overwhelm": 32,
      "sadness": 32
    },
    "temperature": 0.7,
    "confidence_threshold": 0.5,
    "training_command": "python -m training.train_canonical_emotion --language all --dataset realistic --mode all",
    "validation_metrics": {
      "accuracy": 1.0,
      "macro_f1": 1.0,
      "coverage_at_threshold": 1.0
    }
  },
  "zh_lightweight": {
    "language": "zh",
    "backbone_name": "Johnson8187/Chinese-Emotion-Small",
    "backbone_applied_in_training": true,
    "backbone_runtime_status": "direct_classifier",
    "training_mode": "lightweight_tfidf_head",
    "dataset_name": "realistic",
    "split_policy": "grouped_hash_by_source_group_70_20_10",
    "label_schema_version": "canonical_v1",
    "train_size": 192,
    "validation_size": 48,
    "test_size": 16,
    "label_distribution": {
      "anger": 32,
      "anxiety": 32,
      "gratitude": 32,
      "joy": 32,
      "loneliness": 32,
      "neutral": 32,
      "overwhelm": 32,
      "sadness": 32
    },
    "temperature": 0.7,
    "confidence_threshold": 0.5,
    "training_command": "python -m training.train_canonical_emotion --language all --dataset realistic --mode all",
    "validation_metrics": {
      "accuracy": 1.0,
      "macro_f1": 1.0,
      "coverage_at_threshold": 1.0
    }
  },
  "vi_transformer": {
    "language": "vi",
    "backbone_name": "visolex/phobert-emotion",
    "backbone_applied_in_training": true,
    "backbone_runtime_status": "direct_classifier",
    "training_mode": "transformer_frozen_backbone_classifier_head",
    "dataset_name": "realistic",
    "split_policy": "grouped_hash_by_source_group_70_20_10",
    "label_schema_version": "canonical_v1",
    "train_size": 192,
    "validation_size": 40,
    "test_size": 24,
    "label_distribution": {
      "anger": 32,
      "anxiety": 32,
      "gratitude": 32,
      "joy": 32,
      "loneliness": 32,
      "neutral": 32,
      "overwhelm": 32,
      "sadness": 32
    },
    "temperature": 0.7,
    "confidence_threshold": 0.5,
    "training_command": "python -m training.train_canonical_emotion --language all --dataset realistic --mode all",
    "validation_metrics": {
      "accuracy": 0.8,
      "macro_f1": 0.815,
      "coverage_at_threshold": 0.675
    }
  },
  "zh_transformer": {
    "language": "zh",
    "backbone_name": "Johnson8187/Chinese-Emotion-Small",
    "backbone_applied_in_training": true,
    "backbone_runtime_status": "direct_classifier",
    "training_mode": "transformer_frozen_backbone_classifier_head",
    "dataset_name": "realistic",
    "split_policy": "grouped_hash_by_source_group_70_20_10",
    "label_schema_version": "canonical_v1",
    "train_size": 192,
    "validation_size": 48,
    "test_size": 16,
    "label_distribution": {
      "anger": 32,
      "anxiety": 32,
      "gratitude": 32,
      "joy": 32,
      "loneliness": 32,
      "neutral": 32,
      "overwhelm": 32,
      "sadness": 32
    },
    "temperature": 1.0,
    "confidence_threshold": 0.6,
    "training_command": "python -m training.train_canonical_emotion --language all --dataset realistic --mode all",
    "validation_metrics": {
      "accuracy": 0.333,
      "macro_f1": 0.296,
      "coverage_at_threshold": 0.062
    }
  }
}
```

## Metrics

| system | accuracy | macro_f1 | coverage |
| --- | ---: | ---: | ---: |
| legacy heuristic | 0.125 | 0.028 | 1.0 |
| public direct-mapping | 0.312 | 0.286 | 0.0 |
| lightweight canonical | 1.0 | 1.0 | 1.0 |
| transformer canonical | 1.0 | 1.0 | 1.0 |

## Per-Class F1
```json
{
  "legacy": {
    "anger": 0.0,
    "anxiety": 0.0,
    "gratitude": 0.0,
    "joy": 0.0,
    "loneliness": 0.0,
    "neutral": 0.222,
    "overwhelm": 0.0,
    "sadness": 0.0
  },
  "public": {
    "anger": 0.667,
    "anxiety": 0.4,
    "gratitude": 0.0,
    "joy": 0.0,
    "loneliness": 1.0,
    "neutral": 0.222,
    "overwhelm": 0.0,
    "sadness": 0.0
  },
  "lightweight": {
    "anger": 1.0,
    "anxiety": 1.0,
    "gratitude": 1.0,
    "joy": 1.0,
    "loneliness": 1.0,
    "neutral": 1.0,
    "overwhelm": 1.0,
    "sadness": 1.0
  },
  "transformer": {
    "anger": 1.0,
    "anxiety": 1.0,
    "gratitude": 1.0,
    "joy": 1.0,
    "loneliness": 1.0,
    "neutral": 1.0,
    "overwhelm": 1.0,
    "sadness": 1.0
  }
}
```

## Per-Language Breakdown
```json
{
  "legacy": {
    "en": {
      "accuracy": 0.125,
      "macro_f1": 0.028
    }
  },
  "public": {
    "en": {
      "accuracy": 0.312,
      "macro_f1": 0.286
    }
  },
  "lightweight": {
    "en": {
      "accuracy": 1.0,
      "macro_f1": 1.0
    }
  },
  "transformer": {
    "en": {
      "accuracy": 1.0,
      "macro_f1": 1.0
    }
  }
}
```

## Confusion Matrix: Transformer Canonical
| gold \ pred | anger | anxiety | gratitude | joy | loneliness | neutral | overwhelm | sadness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anger | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| anxiety | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| gratitude | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| joy | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| loneliness | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| neutral | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| overwhelm | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| sadness | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |

## Representative Transformer Errors
| id | language | group | gold | pred | confidence | provider | text |
| --- | --- | --- | --- | --- | ---: | --- | --- |

## Representative Lightweight Errors
| id | language | group | gold | pred | confidence | provider | text |
| --- | --- | --- | --- | --- | ---: | --- | --- |

## Representative Public Errors
| id | language | group | gold | pred | confidence | provider | text |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| en-real-089 | en | family_health_v3 | joy | neutral | 0.35 | heuristic_fallback | At the end of today, My family member looked a little stronger today, and I felt a real wave of relief. I just wanted to name that plainly. |
| en-real-090 | en | family_health_v3 | sadness | neutral | 0.35 | heuristic_fallback | At the end of today, Seeing someone I love this tired keeps sitting heavy in my chest. I just wanted to name that plainly. |
| en-real-093 | en | family_health_v3 | overwhelm | neutral | 0.35 | heuristic_fallback | At the end of today, There are too many practical and emotional pieces to hold at the same time. I just wanted to name that plainly. |
| en-real-094 | en | family_health_v3 | gratitude | neutral | 0.35 | heuristic_fallback | At the end of today, I am deeply grateful for everyone who has been helping us through this. I just wanted to name that plainly. |
| en-real-097 | en | self_doubt_v0 | joy | neutral | 0.35 | heuristic_fallback | Tonight, I handled one hard thing better than I expected, and that gave me a small boost. I am trying to be honest about that. |
| en-real-098 | en | self_doubt_v0 | sadness | neutral | 0.35 | heuristic_fallback | Tonight, I keep landing on the thought that I am falling short again. I am trying to be honest about that. |
| en-real-099 | en | self_doubt_v0 | anxiety | neutral | 0.35 | heuristic_fallback | Tonight, I am scared people will notice how unsure I actually feel. I am trying to be honest about that. |
| en-real-100 | en | self_doubt_v0 | anger | neutral | 0.35 | heuristic_fallback | Tonight, I am annoyed with myself for spiraling over the same insecurity again. I am trying to be honest about that. |
| en-real-101 | en | self_doubt_v0 | overwhelm | neutral | 0.35 | heuristic_fallback | Tonight, The pressure I put on myself feels like too much right now. I am trying to be honest about that. |
| en-real-102 | en | self_doubt_v0 | gratitude | neutral | 0.35 | heuristic_fallback | Tonight, Someone reflected something kind back to me today and I am holding onto that. I am trying to be honest about that. |

Conclusion:
- Transformer canonical does not beat the old lightweight canonical head on the grouped realistic holdout.
- Transformer canonical beats the public direct-mapping path.
- Transformer canonical beats the legacy heuristic path.
