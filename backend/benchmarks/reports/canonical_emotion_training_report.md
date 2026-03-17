# Canonical Emotion Training Report

Exact commands run:
```bash
python -m training.train_canonical_emotion --language all
python -m benchmarks.evaluate_canonical_models
```

Selected stack:
```json
{
  "enable_canonical_models": true,
  "enable_public_text_models": true,
  "enable_heuristic_fallback": true,
  "vi_public_model": "visolex/phobert-emotion",
  "zh_public_model": "Johnson8187/Chinese-Emotion-Small",
  "multilingual_model": "MilaNLProc/xlm-emo-t",
  "vi_canonical_dir": "backend/models/vi_canonical_emotion",
  "zh_canonical_dir": "backend/models/zh_canonical_emotion",
  "vi_canonical_backbone": "visolex/phobert-emotion",
  "zh_canonical_backbone": "Johnson8187/Chinese-Emotion-Small",
  "ai_confidence_threshold": 0.5,
  "ai_low_confidence_hybrid": true
}
```

Dataset sizes:
- total: 320
- test: 30
- vi total: 160
- zh total: 160

Label distribution:
```json
{
  "anger": 40,
  "anxiety": 40,
  "gratitude": 40,
  "joy": 40,
  "loneliness": 40,
  "neutral": 40,
  "overwhelm": 40,
  "sadness": 40
}
```

Training settings:
```json
{
  "vi": {
    "language": "vi",
    "backbone_name": "visolex/phobert-emotion",
    "backbone_applied_in_training": true,
    "backbone_runtime_status": "direct_classifier",
    "label_schema_version": "canonical_v1",
    "train_size": 116,
    "validation_size": 26,
    "test_size": 18,
    "label_distribution": {
      "anger": 20,
      "anxiety": 20,
      "gratitude": 20,
      "joy": 20,
      "loneliness": 20,
      "neutral": 20,
      "overwhelm": 20,
      "sadness": 20
    },
    "temperature": 0.7,
    "confidence_threshold": 0.5,
    "train_settings": {
      "classifier": "tfidf(word+char) + logistic_regression",
      "regressor": "tfidf(word+char) + ridge",
      "weak_features": true
    },
    "validation_metrics": {
      "accuracy": 1.0,
      "macro_f1": 1.0,
      "coverage_at_threshold": 1.0
    }
  },
  "zh": {
    "language": "zh",
    "backbone_name": "Johnson8187/Chinese-Emotion-Small",
    "backbone_applied_in_training": true,
    "backbone_runtime_status": "direct_classifier",
    "label_schema_version": "canonical_v1",
    "train_size": 110,
    "validation_size": 38,
    "test_size": 12,
    "label_distribution": {
      "anger": 20,
      "anxiety": 20,
      "gratitude": 20,
      "joy": 20,
      "loneliness": 20,
      "neutral": 20,
      "overwhelm": 20,
      "sadness": 20
    },
    "temperature": 0.7,
    "confidence_threshold": 0.5,
    "train_settings": {
      "classifier": "tfidf(word+char) + logistic_regression",
      "regressor": "tfidf(word+char) + ridge",
      "weak_features": true
    },
    "validation_metrics": {
      "accuracy": 1.0,
      "macro_f1": 1.0,
      "coverage_at_threshold": 1.0
    }
  }
}
```

## Metrics

| system | accuracy | macro_f1 | coverage |
| --- | ---: | ---: | ---: |
| legacy heuristic | 0.267 | 0.211 | 1.0 |
| public-model direct | 0.467 | 0.396 | 1.0 |
| canonical fine-tuned | 1.0 | 1.0 | 1.0 |

## Per-Language Breakdown
```json
{
  "legacy": {
    "vi": {
      "accuracy": 0.222,
      "macro_f1": 0.194
    },
    "zh": {
      "accuracy": 0.333,
      "macro_f1": 0.125
    }
  },
  "public": {
    "vi": {
      "accuracy": 0.222,
      "macro_f1": 0.111
    },
    "zh": {
      "accuracy": 0.833,
      "macro_f1": 0.7
    }
  },
  "canonical": {
    "vi": {
      "accuracy": 1.0,
      "macro_f1": 1.0
    },
    "zh": {
      "accuracy": 1.0,
      "macro_f1": 1.0
    }
  }
}
```

## Confusion Matrix: Canonical Fine-Tuned
| gold \ pred | anger | anxiety | gratitude | joy | neutral | overwhelm | sadness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anger | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| anxiety | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| gratitude | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| joy | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| neutral | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| overwhelm | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| sadness | 0 | 0 | 0 | 0 | 0 | 0 | 4 |

## Representative Canonical Errors
| id | language | gold | pred | confidence | provider | text |
| --- | --- | --- | --- | ---: | --- | --- |

## Representative Public-Model Errors
| id | language | gold | pred | confidence | provider | text |
| --- | --- | --- | --- | ---: | --- | --- |
| vi-062 | vi | anger | sadness | 0.98 | visolex/phobert-emotion | Hôm nay mình khó chịu rõ rệt khi nghe cách họ nói chuyện với mình. Sau khi nói chuyện với một người thân, cảm giác này hiện ra rõ hơn. Mình cần chút khoảng cách để đỡ phản ứng quá mạnh. |
| vi-066 | vi | anger | sadness | 0.76 | visolex/phobert-emotion | Mình bực vì lại bị giao phần lỗi mà không ai hỏi mình trước. Công việc chạm deadline nên mình để ý cảm xúc rõ hơn. Mình cần chút khoảng cách để đỡ phản ứng quá mạnh. |
| vi-067 | vi | anger | sadness | 0.88 | visolex/phobert-emotion | Hôm nay mình khó chịu rõ rệt khi nghe cách họ nói chuyện với mình. Sau khi nói chuyện với một người thân, cảm giác này hiện ra rõ hơn. Mình không muốn bùng nổ nhưng thật sự đang khó chịu. |
| vi-072 | vi | anger | sadness | 0.98 | visolex/phobert-emotion | Hôm nay mình khó chịu rõ rệt khi nghe cách họ nói chuyện với mình. Sau khi nói chuyện với một người thân, cảm giác này hiện ra rõ hơn. Mình cần chút khoảng cách để đỡ phản ứng quá mạnh. |
| vi-076 | vi | anger | sadness | 0.76 | visolex/phobert-emotion | Mình bực vì lại bị giao phần lỗi mà không ai hỏi mình trước. Công việc chạm deadline nên mình để ý cảm xúc rõ hơn. Mình cần chút khoảng cách để đỡ phản ứng quá mạnh. |
| vi-077 | vi | anger | sadness | 0.88 | visolex/phobert-emotion | Hôm nay mình khó chịu rõ rệt khi nghe cách họ nói chuyện với mình. Sau khi nói chuyện với một người thân, cảm giác này hiện ra rõ hơn. Mình không muốn bùng nổ nhưng thật sự đang khó chịu. |
| vi-082 | vi | overwhelm | sadness | 0.88 | visolex/phobert-emotion | Hôm nay mọi thứ đến quá nhanh, mình có cảm giác không theo kịp. Công việc chạm deadline nên mình để ý cảm xúc rõ hơn. Cảm giác như đầu óc không còn khoảng trống. |
| vi-092 | vi | overwhelm | sadness | 0.88 | visolex/phobert-emotion | Hôm nay mọi thứ đến quá nhanh, mình có cảm giác không theo kịp. Công việc chạm deadline nên mình để ý cảm xúc rõ hơn. Cảm giác như đầu óc không còn khoảng trống. |
| vi-103 | vi | gratitude | joy | 0.94 | visolex/phobert-emotion | Mình biết ơn vì đồng nghiệp đã đỡ cho mình một phần việc mà không làm mình xấu hổ. Sau khi nói chuyện với một người thân, cảm giác này hiện ra rõ hơn. Nhờ vậy mà mình bớt co lại hơn. |
| vi-105 | vi | gratitude | joy | 0.93 | visolex/phobert-emotion | Mình có cảm giác được đỡ lấy nên lòng mình dịu đi khá nhiều. Khi mở lại danh sách việc cần làm mình thấy rõ trạng thái của mình hơn. Nhờ vậy mà mình bớt co lại hơn. |

Conclusion:
The canonical fine-tuned path beats the current public-model direct-mapping baseline on this offline holdout.
