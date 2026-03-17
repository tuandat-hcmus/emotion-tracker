# AI Core Smoke Outputs

## Selected Config
```json
{
  "enable_canonical_models": true,
  "enable_public_text_models": true,
  "enable_audio_emotion": false,
  "enable_heuristic_fallback": true,
  "ai_confidence_threshold": 0.5,
  "ai_low_confidence_hybrid": true,
  "vi_public_model": "visolex/phobert-emotion",
  "zh_public_model": "Johnson8187/Chinese-Emotion-Small",
  "multilingual_model": "MilaNLProc/xlm-emo-t",
  "audio_model": "SenseVoiceSmall",
  "vi_canonical_dir": "backend/models/vi_canonical_emotion",
  "zh_canonical_dir": "backend/models/zh_canonical_emotion",
  "vi_canonical_backbone": "visolex/phobert-emotion",
  "zh_canonical_backbone": "Johnson8187/Chinese-Emotion-Small"
}
```

## Vietnamese Normalized Output
```json
{
  "label": "biết ơn",
  "emotion_label": "biết ơn",
  "valence_score": 0.69,
  "energy_score": 0.44,
  "stress_score": 0.11,
  "social_need_score": 0.12,
  "confidence": 0.76,
  "dominant_signals": [
    "positive_affect",
    "gratitude_warmth"
  ],
  "response_mode": "celebratory_warm",
  "language": "vi",
  "primary_emotion": "gratitude",
  "secondary_emotions": [
    "joy",
    "neutral"
  ],
  "source": "text",
  "raw_model_labels": [
    "gratitude:0.7584",
    "joy:0.2165",
    "neutral:0.0194",
    "anger:0.0021",
    "loneliness:0.0015",
    "anxiety:0.0009",
    "sadness:0.0007",
    "overwhelm:0.0004"
  ],
  "provider_name": "vi_canonical_emotion",
  "source_metadata": {
    "text": {
      "language": "vi",
      "provider_name": "vi_canonical_emotion",
      "raw_model_labels": [
        "gratitude:0.7584",
        "joy:0.2165",
        "neutral:0.0194",
        "anger:0.0021",
        "loneliness:0.0015",
        "anxiety:0.0009",
        "sadness:0.0007",
        "overwhelm:0.0004"
      ],
      "ranked_emotions": [
        [
          "gratitude",
          0.7583977537616502
        ],
        [
          "joy",
          0.21651319168894637
        ],
        [
          "neutral",
          0.019381056406519936
        ],
        [
          "anger",
          0.002106849126073408
        ],
        [
          "loneliness",
          0.001521264988566449
        ],
        [
          "anxiety",
          0.0009043644176662943
        ],
        [
          "sadness",
          0.0007370453885664022
        ],
        [
          "overwhelm",
          0.0004384742220109034
        ]
      ],
      "confidence": 0.76,
      "source_metadata": {
        "mode": "canonical_classifier",
        "artifact_dir": "/mnt/c/Users/admin/Desktop/Project/Emotion/backend/models/vi_canonical_emotion",
        "temperature": 0.7,
        "confidence_threshold": 0.5,
        "low_confidence": false,
        "coverage_passed": true,
        "valence": 0.69,
        "energy": 0.44,
        "stress": 0.11,
        "backbone_name": "visolex/phobert-emotion",
        "backbone_runtime_status": "direct_classifier",
        "label_schema_version": "canonical_v1",
        "training_mode": "transformer_frozen_backbone_classifier_head",
        "dataset_name": "realistic",
        "split_policy": "grouped_hash_by_source_group_70_20_10",
        "labels": [
          "gratitude",
          "joy",
          "neutral",
          "anger",
          "loneliness",
          "anxiety",
          "sadness",
          "overwhelm"
        ]
      }
    },
    "audio": null,
    "fusion_weights": {
      "text": 1.0,
      "audio": 0.0
    }
  }
}
```

## Chinese Normalized Output
```json
{
  "label": "nặng nề",
  "emotion_label": "nặng nề",
  "valence_score": -0.35,
  "energy_score": 0.64,
  "stress_score": 0.65,
  "social_need_score": 0.12,
  "confidence": 0.98,
  "dominant_signals": [
    "sadness_weight"
  ],
  "response_mode": "validating_gentle",
  "language": "zh",
  "primary_emotion": "sadness",
  "secondary_emotions": [
    "anxiety",
    "overwhelm"
  ],
  "source": "text",
  "raw_model_labels": [
    "anxiety:0.3575",
    "overwhelm:0.2619",
    "sadness:0.1197",
    "joy:0.0753",
    "loneliness:0.0744",
    "anger:0.0713",
    "gratitude:0.037",
    "neutral:0.0028",
    "LABEL_4",
    "LABEL_0",
    "LABEL_5",
    "LABEL_7",
    "LABEL_1",
    "LABEL_3",
    "LABEL_6",
    "LABEL_2"
  ],
  "provider_name": "zh_canonical_emotion+Johnson8187/Chinese-Emotion-Small",
  "source_metadata": {
    "text": {
      "language": "zh",
      "provider_name": "zh_canonical_emotion+Johnson8187/Chinese-Emotion-Small",
      "raw_model_labels": [
        "anxiety:0.3575",
        "overwhelm:0.2619",
        "sadness:0.1197",
        "joy:0.0753",
        "loneliness:0.0744",
        "anger:0.0713",
        "gratitude:0.037",
        "neutral:0.0028",
        "LABEL_4",
        "LABEL_0",
        "LABEL_5",
        "LABEL_7",
        "LABEL_1",
        "LABEL_3",
        "LABEL_6",
        "LABEL_2"
      ],
      "ranked_emotions": [
        [
          "sadness",
          0.3763134687674361
        ],
        [
          "anxiety",
          0.25104713007357127
        ],
        [
          "overwhelm",
          0.1833147251462569
        ],
        [
          "joy",
          0.05289043710494038
        ],
        [
          "loneliness",
          0.05211132192274097
        ],
        [
          "anger",
          0.05151793692110075
        ],
        [
          "gratitude",
          0.025920073424656746
        ],
        [
          "neutral",
          0.006884935015531629
        ]
      ],
      "confidence": 0.98,
      "source_metadata": {
        "mode": "canonical_hybrid",
        "canonical": {
          "language": "zh",
          "provider_name": "zh_canonical_emotion",
          "raw_model_labels": [
            "anxiety:0.3575",
            "overwhelm:0.2619",
            "sadness:0.1197",
            "joy:0.0753",
            "loneliness:0.0744",
            "anger:0.0713",
            "gratitude:0.037",
            "neutral:0.0028"
          ],
          "ranked_emotions": [
            [
              "anxiety",
              0.3575237017925319
            ],
            [
              "overwhelm",
              0.261878178780367
            ],
            [
              "sadness",
              0.11967900388756209
            ],
            [
              "joy",
              0.07526611256076018
            ],
            [
              "loneliness",
              0.07444474560391567
            ],
            [
              "anger",
              0.07133972339914801
            ],
            [
              "gratitude",
              0.03702867632093821
            ],
            [
              "neutral",
              0.0028398576547769548
            ]
          ],
          "confidence": 0.36,
          "source_metadata": {
            "mode": "canonical_classifier",
            "artifact_dir": "/mnt/c/Users/admin/Desktop/Project/Emotion/backend/models/zh_canonical_emotion",
            "temperature": 1.0,
            "confidence_threshold": 0.6,
            "low_confidence": true,
            "coverage_passed": false,
            "valence": -0.35,
            "energy": 0.64,
            "stress": 0.65,
            "backbone_name": "Johnson8187/Chinese-Emotion-Small",
            "backbone_runtime_status": "direct_classifier",
            "label_schema_version": "canonical_v1",
            "training_mode": "transformer_frozen_backbone_classifier_head",
            "dataset_name": "realistic",
            "split_policy": "grouped_hash_by_source_group_70_20_10",
            "labels": [
              "anxiety",
              "overwhelm",
              "sadness",
              "joy",
              "loneliness",
              "anger",
              "gratitude",
              "neutral"
            ]
          }
        },
        "public": {
          "language": "zh",
          "provider_name": "Johnson8187/Chinese-Emotion-Small",
          "raw_model_labels": [
            "LABEL_4",
            "LABEL_0",
            "LABEL_5",
            "LABEL_7",
            "LABEL_1",
            "LABEL_3",
            "LABEL_6",
            "LABEL_2"
          ],
          "ranked_emotions": [
            [
              "sadness",
              0.9751272201538086
            ],
            [
              "neutral",
              0.016323448857292533
            ],
            [
              "anger",
              0.005267101805657148
            ],
            [
              "anxiety",
              0.0026017960626631975
            ],
            [
              "joy",
              0.0006805277080275118
            ]
          ],
          "confidence": 0.98,
          "source_metadata": {
            "mode": "transformers",
            "model_name": "Johnson8187/Chinese-Emotion-Small",
            "model_key": "zh-public",
            "cache_complete": true,
            "family": "public",
            "task_type": "text-classification",
            "valence": -0.55,
            "energy": 0.23,
            "stress": 0.36
          }
        },
        "low_confidence": true,
        "hybrid_weight": 0.7,
        "coverage_passed": false,
        "valence": -0.35,
        "energy": 0.64,
        "stress": 0.65
      }
    },
    "audio": null,
    "fusion_weights": {
      "text": 1.0,
      "audio": 0.0
    }
  }
}
```

## Processed Check-In
```json
{
  "entry_id": "53b19750-5a90-4290-bc6e-56e0aefa66d0",
  "status": "processed",
  "user_id": "smoke-user",
  "session_type": "free",
  "audio_path": "/tmp/tmp8n3cdgqa/dummy.wav",
  "transcript_text": "Hôm nay mình thấy khá nhẹ nhõm và biết ơn vì mọi thứ dần ổn hơn.",
  "transcript_confidence": 1.0,
  "ai_response": "Có một sự ấm lại rất rõ trong điều bạn vừa kể về biết ơn/thành tựu. Cảm giác biết ơn đó đáng để giữ lại thêm một chút. You can meet today one honest check-in at a time.",
  "emotion_label": "biết ơn",
  "valence_score": 0.69,
  "energy_score": 0.44,
  "stress_score": 0.11,
  "social_need_score": 0.12,
  "confidence": 0.76,
  "dominant_signals": [
    "positive_affect",
    "gratitude_warmth"
  ],
  "response_mode": "celebratory_warm",
  "language": "vi",
  "primary_emotion": "gratitude",
  "secondary_emotions": [
    "joy",
    "neutral"
  ],
  "source": "text",
  "raw_model_labels": [
    "gratitude:0.7584",
    "joy:0.2165",
    "neutral:0.0194",
    "anger:0.0021",
    "loneliness:0.0015",
    "anxiety:0.0009",
    "sadness:0.0007",
    "overwhelm:0.0004"
  ],
  "provider_name": "vi_canonical_emotion",
  "empathetic_response": "Có một sự ấm lại rất rõ trong điều bạn vừa kể về biết ơn/thành tựu. Cảm giác biết ơn đó đáng để giữ lại thêm một chút.",
  "gentle_suggestion": null,
  "quote_text": "You can meet today one honest check-in at a time.",
  "response_metadata": {
    "emotion_analysis": {
      "language": "vi",
      "primary_emotion": "gratitude",
      "secondary_emotions": [
        "joy",
        "neutral"
      ],
      "social_need_score": 0.12,
      "confidence": 0.76,
      "dominant_signals": [
        "positive_affect",
        "gratitude_warmth"
      ],
      "response_mode": "celebratory_warm",
      "source": "text",
      "raw_model_labels": [
        "gratitude:0.7584",
        "joy:0.2165",
        "neutral:0.0194",
        "anger:0.0021",
        "loneliness:0.0015",
        "anxiety:0.0009",
        "sadness:0.0007",
        "overwhelm:0.0004"
      ],
      "provider_name": "vi_canonical_emotion",
      "source_metadata": {
        "text": {
          "language": "vi",
          "provider_name": "vi_canonical_emotion",
          "raw_model_labels": [
            "gratitude:0.7584",
            "joy:0.2165",
            "neutral:0.0194",
            "anger:0.0021",
            "loneliness:0.0015",
            "anxiety:0.0009",
            "sadness:0.0007",
            "overwhelm:0.0004"
          ],
          "ranked_emotions": [
            [
              "gratitude",
              0.7583977537616502
            ],
            [
              "joy",
              0.21651319168894637
            ],
            [
              "neutral",
              0.019381056406519936
            ],
            [
              "anger",
              0.002106849126073408
            ],
            [
              "loneliness",
              0.001521264988566449
            ],
            [
              "anxiety",
              0.0009043644176662943
            ],
            [
              "sadness",
              0.0007370453885664022
            ],
            [
              "overwhelm",
              0.0004384742220109034
            ]
          ],
          "confidence": 0.76,
          "source_metadata": {
            "mode": "canonical_classifier",
            "artifact_dir": "/mnt/c/Users/admin/Desktop/Project/Emotion/backend/models/vi_canonical_emotion",
            "temperature": 0.7,
            "confidence_threshold": 0.5,
            "low_confidence": false,
            "coverage_passed": true,
            "valence": 0.69,
            "energy": 0.44,
            "stress": 0.11,
            "backbone_name": "visolex/phobert-emotion",
            "backbone_runtime_status": "direct_classifier",
            "label_schema_version": "canonical_v1",
            "training_mode": "transformer_frozen_backbone_classifier_head",
            "dataset_name": "realistic",
            "split_policy": "grouped_hash_by_source_group_70_20_10",
            "labels": [
              "gratitude",
              "joy",
              "neutral",
              "anger",
              "loneliness",
              "anxiety",
              "sadness",
              "overwhelm"
            ]
          }
        },
        "audio": null,
        "fusion_weights": {
          "text": 1.0,
          "audio": 0.0
        }
      }
    },
    "response_plan": {
      "opening_style": "warm_appreciation",
      "acknowledgment_focus": "what_is_working",
      "suggestion_allowed": false,
      "suggestion_style": "none",
      "quote_allowed": true,
      "avoid_advice": true,
      "tone": "warm_light",
      "max_sentences": 2
    },
    "quote": {
      "short_text": "You can meet today one honest check-in at a time.",
      "tone": "neutral",
      "source_type": "curated"
    }
  },
  "topic_tags": [
    "biết ơn/thành tựu",
    "đời sống hằng ngày"
  ],
  "risk_level": "low",
  "risk_flags": [],
  "created_at": "2026-03-17 14:01:06",
  "updated_at": "2026-03-17 14:01:06.742181"
}
```
