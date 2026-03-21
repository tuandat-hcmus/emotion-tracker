from app.services.companion_core import build_companion_pipeline
from app.services.topic_service import tag_topics


ENGLISH_STATE_CASES = [
    {
        "text": "My girlfriend seems sad now",
        "emotion_analysis": {
            "language": "en",
            "primary_emotion": "sadness",
            "secondary_emotions": ["anger", "joy"],
            "emotion_label": "sadness",
            "valence_score": -0.52,
            "energy_score": 0.25,
            "stress_score": 0.37,
            "social_need_score": 0.14,
            "confidence": 0.93,
            "dominant_signals": ["sadness_weight", "mixed_emotions"],
            "response_mode": "low_energy_comfort",
            "source": "text",
            "raw_model_labels": ["sadness", "anger", "joy"],
            "provider_name": "MilaNLProc/xlm-emo-t",
            "source_metadata": {},
        },
        "expected": {
            "primary_emotion": "anxiety",
            "emotion_owner": "user",
            "user_stance": "worried_about_other",
            "concern_target": "girlfriend",
            "relationship_role": "girlfriend",
            "event_type": "other_person_distress",
            "strategy_type": "supportive_reflective",
        },
    },
    {
        "text": "My crush don't like me",
        "emotion_analysis": {
            "language": "en",
            "primary_emotion": "sadness",
            "secondary_emotions": ["anxiety"],
            "emotion_label": "sadness",
            "valence_score": -0.44,
            "energy_score": 0.24,
            "stress_score": 0.33,
            "social_need_score": 0.18,
            "confidence": 0.71,
            "dominant_signals": ["sadness_weight"],
            "response_mode": "supportive_reflective",
            "source": "text",
            "raw_model_labels": ["sadness", "anxiety"],
            "provider_name": "test-model",
            "source_metadata": {},
        },
        "expected": {
            "primary_emotion": "sadness",
            "emotion_owner": "user",
            "user_stance": "hurt_by_rejection",
            "concern_target": "crush",
            "relationship_role": "crush",
            "event_type": "uncertain_romantic_rejection",
            "strategy_type": "low_energy_comfort",
        },
    },
    {
        "text": "Thanh Minh seems angry now because I didn't finish the deadline on time",
        "emotion_analysis": {
            "language": "en",
            "primary_emotion": "anger",
            "secondary_emotions": ["sadness"],
            "emotion_label": "anger",
            "valence_score": -0.49,
            "energy_score": 0.61,
            "stress_score": 0.58,
            "social_need_score": 0.11,
            "confidence": 0.76,
            "dominant_signals": ["anger_friction"],
            "response_mode": "validating_gentle",
            "source": "text",
            "raw_model_labels": ["anger", "sadness"],
            "provider_name": "test-model",
            "source_metadata": {},
        },
        "expected": {
            "primary_emotion": "anxiety",
            "emotion_owner": "user",
            "user_stance": "guilty_toward_other",
            "concern_target": "Thanh Minh",
            "relationship_role": "named_person",
            "event_type": "responsibility_tension",
            "strategy_type": "validating_gentle",
        },
    },
    {
        "text": "I let my teammate down and I keep replaying it",
        "emotion_analysis": {
            "language": "en",
            "primary_emotion": "sadness",
            "secondary_emotions": ["anxiety"],
            "emotion_label": "sadness",
            "valence_score": -0.46,
            "energy_score": 0.41,
            "stress_score": 0.53,
            "social_need_score": 0.1,
            "confidence": 0.66,
            "dominant_signals": ["sadness_weight"],
            "response_mode": "supportive_reflective",
            "source": "text",
            "raw_model_labels": ["sadness", "anxiety"],
            "provider_name": "test-model",
            "source_metadata": {},
        },
        "expected": {
            "primary_emotion": "anxiety",
            "emotion_owner": "user",
            "user_stance": "guilty_toward_other",
            "concern_target": "teammate",
            "relationship_role": "teammate",
            "event_type": "responsibility_tension",
            "strategy_type": "validating_gentle",
        },
    },
    {
        "text": "A friend told me I'd be good at helping people solve problems",
        "emotion_analysis": {
            "language": "en",
            "primary_emotion": "joy",
            "secondary_emotions": ["neutral"],
            "emotion_label": "joy",
            "valence_score": 0.31,
            "energy_score": 0.34,
            "stress_score": 0.19,
            "social_need_score": 0.08,
            "confidence": 0.58,
            "dominant_signals": ["positive_affect"],
            "response_mode": "supportive_reflective",
            "source": "text",
            "raw_model_labels": ["joy"],
            "provider_name": "test-model",
            "source_metadata": {},
        },
        "expected": {
            "primary_emotion": "gratitude",
            "emotion_owner": "user",
            "user_stance": "encouraged_by_other",
            "concern_target": "friend",
            "relationship_role": "friend",
            "event_type": "recognition_or_praise",
            "strategy_type": "celebratory_warm",
        },
    },
    {
        "text": "I keep feeling left out lately, like everyone already has their people",
        "emotion_analysis": {
            "language": "en",
            "primary_emotion": "loneliness",
            "secondary_emotions": ["sadness"],
            "emotion_label": "loneliness",
            "valence_score": -0.66,
            "energy_score": 0.26,
            "stress_score": 0.42,
            "social_need_score": 0.5,
            "confidence": 0.73,
            "dominant_signals": ["loneliness_pull", "connection_need"],
            "response_mode": "low_energy_comfort",
            "source": "text",
            "raw_model_labels": ["loneliness", "sadness"],
            "provider_name": "test-model",
            "source_metadata": {},
        },
        "expected": {
            "primary_emotion": "loneliness",
            "emotion_owner": "user",
            "user_stance": "processing_self",
            "concern_target": None,
            "relationship_role": None,
            "event_type": "loneliness_or_disconnection",
            "strategy_type": "low_energy_comfort",
        },
    },
    {
        "text": "I'm relieved the exam is over, but I still feel weirdly empty",
        "emotion_analysis": {
            "language": "en",
            "primary_emotion": "sadness",
            "secondary_emotions": ["joy"],
            "emotion_label": "mixed",
            "valence_score": -0.18,
            "energy_score": 0.24,
            "stress_score": 0.22,
            "social_need_score": 0.08,
            "confidence": 0.64,
            "dominant_signals": ["mixed_emotions", "relief_release"],
            "response_mode": "supportive_reflective",
            "source": "text",
            "raw_model_labels": ["sadness", "joy"],
            "provider_name": "test-model",
            "source_metadata": {},
        },
        "expected": {
            "primary_emotion": "sadness",
            "emotion_owner": "user",
            "user_stance": "processing_self",
            "concern_target": None,
            "relationship_role": None,
            "event_type": "uncertain_mixed_state",
            "strategy_type": "low_energy_comfort",
        },
    },
]


def _run_case(text: str, emotion_analysis: dict[str, object]):
    topic_tags = tag_topics(text)
    pipeline = build_companion_pipeline(
        transcript=text,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level="low",
    )
    return pipeline.normalized_state, pipeline.support_strategy


def _case_mismatches(expected: dict[str, object], state, strategy) -> dict[str, object]:
    actual = {
        "primary_emotion": state.primary_emotion,
        "emotion_owner": state.emotion_owner,
        "user_stance": state.user_stance,
        "concern_target": state.concern_target,
        "relationship_role": state.relationship_role,
        "event_type": state.event_type,
        "strategy_type": strategy.strategy_type,
    }
    return {
        field: {"expected": expected[field], "actual": actual[field]}
        for field in expected
        if actual[field] != expected[field]
    }


def test_english_state_eval_suite_scores_target_failure_patterns() -> None:
    scores = {
        "primary_emotion": 0,
        "emotion_owner": 0,
        "user_stance": 0,
        "concern_target": 0,
        "relationship_role": 0,
        "event_type": 0,
        "strategy_type": 0,
    }
    failing_cases: list[dict[str, object]] = []

    for case in ENGLISH_STATE_CASES:
        state, strategy = _run_case(case["text"], case["emotion_analysis"])
        expected = case["expected"]
        mismatches = _case_mismatches(expected, state, strategy)

        scores["primary_emotion"] += state.primary_emotion == expected["primary_emotion"]
        scores["emotion_owner"] += state.emotion_owner == expected["emotion_owner"]
        scores["user_stance"] += state.user_stance == expected["user_stance"]
        scores["concern_target"] += state.concern_target == expected["concern_target"]
        scores["relationship_role"] += state.relationship_role == expected["relationship_role"]
        scores["event_type"] += state.event_type == expected["event_type"]
        scores["strategy_type"] += strategy.strategy_type == expected["strategy_type"]
        if mismatches:
            failing_cases.append(
                {
                    "text": case["text"],
                    "expected": expected,
                    "mismatches": mismatches,
                }
            )

    total = len(ENGLISH_STATE_CASES)
    assert scores == {
        "primary_emotion": total,
        "emotion_owner": total,
        "user_stance": total,
        "concern_target": total,
        "relationship_role": total,
        "event_type": total,
        "strategy_type": total,
    }, f"Per-case mismatches: {failing_cases}"


def test_responsibility_tension_biases_toward_user_guilt_not_other_person_anger() -> None:
    case = ENGLISH_STATE_CASES[2]
    state, strategy = _run_case(case["text"], case["emotion_analysis"])

    assert state.primary_emotion in {"anxiety", "overwhelm"}
    assert state.emotion_owner == "user"
    assert state.user_stance == "guilty_toward_other"
    assert state.concern_target == "Thanh Minh"
    assert state.event_type == "responsibility_tension"
    assert strategy.strategy_type == "validating_gentle"


def test_recognition_case_avoids_generic_mixed_state_interpretation() -> None:
    case = ENGLISH_STATE_CASES[4]
    state, strategy = _run_case(case["text"], case["emotion_analysis"])

    assert state.primary_emotion == "gratitude"
    assert state.user_stance == "encouraged_by_other"
    assert state.event_type == "recognition_or_praise"
    assert strategy.strategy_type == "celebratory_warm"
