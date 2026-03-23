from app.services.ai_support_service import build_support_package
from app.services.companion_core import build_companion_pipeline, build_emotional_memory_record
from app.services.companion_core.memory_store import get_noop_memory_store
from app.services.companion_core.schemas import InsightFeatures, NormalizedEmotionalState, SupportStrategy


def _sample_state(
    *,
    event_type: str = "deadline_pressure",
    social_context: str = "work_or_school",
    primary_emotion: str = "overwhelm",
    confidence: float = 0.72,
) -> NormalizedEmotionalState:
    return NormalizedEmotionalState(
        language="en",
        primary_emotion=primary_emotion,
        secondary_emotions=["anxiety"],
        valence=-0.52,
        energy=0.62,
        stress=0.81,
        emotion_owner="user",
        social_context=social_context,
        event_type=event_type,
        concern_target=None,
        uncertainty=round(1.0 - confidence, 2),
        confidence=confidence,
        response_mode="grounding_soft",
        risk_level="low",
        topic_tags=["work/school"],
        evidence_spans=["deadlines"],
        source_provider="test-model",
    )


def test_build_companion_pipeline_enriches_response_plan() -> None:
    prior_state = _sample_state()
    prior_strategy = SupportStrategy(
        support_focus="user",
        strategy_type="grounding_soft",
        suggestion_budget="none",
        personalization_tone="gentle",
        response_goal="gentle_orientation",
        rationale=["high emotional load requires grounding rather than advice"],
    )
    prior_record = build_emotional_memory_record(
        user_id="demo-user",
        transcript="Deadlines have been piling up all week.",
        topic_tags=["work/school"],
        risk_level="low",
        normalized_state=prior_state,
        support_strategy=prior_strategy,
        insight_features=InsightFeatures(is_negative_checkin=True, deadline_related=True, high_stress_flag=True),
        response_provider="template",
        response_mode="grounding_soft",
        suggestion_given=False,
    )

    emotion_analysis = {
        "language": "en",
        "primary_emotion": "overwhelm",
        "secondary_emotions": ["anxiety"],
        "emotion_label": "overwhelm",
        "valence_score": -0.48,
        "energy_score": 0.58,
        "stress_score": 0.78,
        "social_need_score": 0.12,
        "confidence": 0.69,
        "dominant_signals": ["stress_pressure", "overwhelm_load"],
        "response_mode": "grounding_soft",
        "source": "text",
        "raw_model_labels": ["overwhelm"],
        "provider_name": "test-model",
        "source_metadata": {"mode": "test"},
    }

    result = build_companion_pipeline(
        transcript="I've had deadlines piling up for days.",
        emotion_analysis=emotion_analysis,
        topic_tags=["work/school"],
        risk_level="low",
        memory_records=[prior_record],
    )

    assert result.render_context.event_type == "deadline_pressure"
    assert result.normalized_state.event_type == "deadline_pressure"
    assert result.memory_summary.recent_checkin_count == 1
    assert result.support_strategy.strategy_type == "stress_supportive"
    assert result.response_plan["normalized_state"]["event_type"] == "deadline_pressure"
    assert result.response_plan["support_strategy"]["strategy_type"] == "stress_supportive"
    assert result.response_plan["memory_context"]["recent_checkin_count"] == 1
    assert result.response_plan["render_context"]["event_type"] == "deadline_pressure"
    assert result.emotion_analysis["stress_score"] >= 0.84
    assert result.emotion_analysis["response_mode"] == "stress_supportive"
    assert "recent_pattern_detected" in result.emotion_analysis["dominant_signals"]
    assert result.normalized_state.uncertainty <= 0.27


def test_recent_context_does_not_override_current_turn_primary_label() -> None:
    prior_state = _sample_state(primary_emotion="overwhelm", event_type="deadline_pressure")
    prior_strategy = SupportStrategy(
        support_focus="user",
        strategy_type="stress_supportive",
        suggestion_budget="none",
        personalization_tone="steady_grounding",
        response_goal="reduce_pressure_spiral",
        rationale=["deadline pressure has repeated recently"],
    )
    prior_record = build_emotional_memory_record(
        user_id="demo-user",
        transcript="Deadlines have been piling up all week.",
        topic_tags=["work/school"],
        risk_level="low",
        normalized_state=prior_state,
        support_strategy=prior_strategy,
        insight_features=InsightFeatures(is_negative_checkin=True, deadline_related=True, high_stress_flag=True),
        response_provider="template",
        response_mode="stress_supportive",
        suggestion_given=False,
    )

    emotion_analysis = {
        "language": "en",
        "primary_label": "joy",
        "secondary_labels": ["neutral"],
        "all_labels": ["joy"],
        "scores": {"anger": 0.01, "disgust": 0.0, "fear": 0.08, "joy": 0.74, "sadness": 0.04, "surprise": 0.03, "neutral": 0.2},
        "threshold": 0.5,
        "primary_emotion": "gratitude",
        "secondary_emotions": ["joy"],
        "valence_score": 0.48,
        "energy_score": 0.42,
        "stress_score": 0.12,
        "social_need_score": 0.1,
        "confidence": 0.72,
        "dominant_signals": ["positive_affect", "gratitude_warmth"],
        "context_tags": ["gratitude", "positive_moment"],
        "response_mode": "celebratory_warm",
        "source": "text",
        "provider_name": "test-model",
        "source_metadata": {"mode": "test"},
    }

    result = build_companion_pipeline(
        transcript="I feel lighter and grateful today.",
        emotion_analysis=emotion_analysis,
        topic_tags=["gratitude/achievement"],
        risk_level="low",
        memory_records=[prior_record],
    )

    assert result.emotion_analysis["primary_label"] == "joy"
    assert result.response_plan["memory_context"]["recent_checkin_count"] == 1
    assert result.insight_features.positive_anchor_candidate is True


def test_build_support_package_exposes_shared_companion_fields(monkeypatch) -> None:
    import app.services.ai_support_service as support_service_module

    monkeypatch.setattr(
        support_service_module,
        "detect_safety_risk",
        lambda _text: {"risk_level": "low", "risk_flags": []},
    )
    monkeypatch.setattr(support_service_module, "tag_topics", lambda _text: ["work/school"])
    monkeypatch.setattr(
        support_service_module,
        "analyze_emotion",
        lambda _text, risk_level, audio_path=None: {
            "language": "en",
            "primary_emotion": "overwhelm",
            "secondary_emotions": ["anxiety"],
            "emotion_label": "overwhelm",
            "valence_score": -0.48,
            "energy_score": 0.58,
            "stress_score": 0.78,
            "social_need_score": 0.12,
            "confidence": 0.69,
            "dominant_signals": ["stress_pressure", "overwhelm_load"],
            "response_mode": "grounding_soft",
            "source": "text",
            "raw_model_labels": ["overwhelm"],
            "provider_name": "test-model",
            "source_metadata": {"mode": "test"},
        },
    )
    monkeypatch.setattr(
        support_service_module,
        "generate_supportive_response",
        lambda **_kwargs: {
            "empathetic_response": "That sounds like a lot of pressure to carry.",
            "gentle_suggestion": None,
            "quote": None,
            "ai_response": "That sounds like a lot of pressure to carry.",
        },
    )

    payload = build_support_package(
        transcript="I've had deadlines piling up for days.",
        user_id="user-1",
    )

    assert payload["emotion_analysis"]["provider_name"] == "test-model"
    assert payload["render_context"]["event_type"] == "deadline_pressure"
    assert payload["normalized_state"]["event_type"] == "deadline_pressure"
    assert payload["support_strategy"]["strategy_type"] == "stress_supportive"
    assert payload["insight_features"]["deadline_related"] is True
    assert payload["memory_summary"]["recent_checkin_count"] == 0
    assert payload["response_plan"]["normalized_state"]["event_type"] == "deadline_pressure"


def test_build_companion_pipeline_shapes_other_person_concern_plan() -> None:
    emotion_analysis = {
        "language": "en",
        "primary_emotion": "sadness",
        "secondary_emotions": ["neutral"],
        "emotion_label": "sadness",
        "valence_score": -0.44,
        "energy_score": 0.22,
        "stress_score": 0.28,
        "social_need_score": 0.12,
        "confidence": 0.66,
        "dominant_signals": ["sadness_weight"],
        "response_mode": "low_energy_comfort",
        "source": "text",
        "raw_model_labels": ["sadness"],
        "provider_name": "test-model",
        "source_metadata": {"mode": "test"},
    }

    result = build_companion_pipeline(
        transcript="My friend Minh seems sad now.",
        emotion_analysis=emotion_analysis,
        topic_tags=["relationships"],
        risk_level="low",
    )

    assert result.render_context.user_stance == "worried_about_other"
    assert result.support_strategy.support_focus == "relationship"
    assert result.response_plan["acknowledgment_focus"] == "care_for_other"
    assert result.response_plan["suggestion_allowed"] is False
    assert result.response_plan["follow_up_question_allowed"] is True
    assert result.response_plan["response_variant"] == "empathy_plus_followup"


def test_noop_memory_store_is_safe_for_production_wiring() -> None:
    store = get_noop_memory_store()
    state = _sample_state()
    strategy = SupportStrategy(
        support_focus="user",
        strategy_type="grounding_soft",
        suggestion_budget="none",
        personalization_tone="gentle",
        response_goal="gentle_orientation",
        rationale=[],
    )
    record = build_emotional_memory_record(
        user_id="user-1",
        transcript="Deadlines have been piling up all week.",
        topic_tags=["work/school"],
        risk_level="low",
        normalized_state=state,
        support_strategy=strategy,
        insight_features=InsightFeatures(is_negative_checkin=True),
        response_provider="template",
        response_mode="grounding_soft",
        suggestion_given=False,
    )

    store.append(record)

    assert store.list_recent("user-1") == []
