from app.services.companion_core.emotion_understanding import build_normalized_emotional_state
from app.services.companion_core.feature_extraction import extract_insight_features
from app.services.companion_core.insight_engine import build_weekly_insight
from app.services.companion_core.memory_store import InMemoryEmotionalMemoryStore
from app.services.companion_core.memory_summary import build_memory_summary
from app.services.companion_core.schemas import EmotionalMemoryRecord, NormalizedEmotionalState
from app.services.companion_core.strategy_engine import select_support_strategy


def _build_state(
    *,
    primary_emotion: str,
    secondary_emotions: list[str],
    valence_score: float,
    energy_score: float,
    stress_score: float,
    confidence: float,
    response_mode: str,
    social_context: str,
    event_type: str,
    concern_target: str | None,
    relationship_concern: bool,
    other_person_state_mentioned: bool,
    evidence_spans: list[str],
    topic_tags: list[str],
) -> NormalizedEmotionalState:
    return build_normalized_emotional_state(
        emotion_analysis={
            "language": "en",
            "primary_emotion": primary_emotion,
            "secondary_emotions": secondary_emotions,
            "valence_score": valence_score,
            "energy_score": energy_score,
            "stress_score": stress_score,
            "confidence": confidence,
            "response_mode": response_mode,
            "provider_name": "test-model",
        },
        render_context={
            "social_context": social_context,
            "event_type": event_type,
            "concern_target": concern_target,
            "other_person_state_mentioned": other_person_state_mentioned,
            "relationship_concern": relationship_concern,
            "evidence_spans": evidence_spans,
        },
        topic_tags=topic_tags,
        risk_level="low",
    )


def _build_record(user_id: str, transcript: str, state) -> EmotionalMemoryRecord:
    strategy = select_support_strategy(state)
    return EmotionalMemoryRecord(
        user_id=user_id,
        transcript=transcript,
        language=state.language,
        normalized_state=state,
        support_strategy=strategy,
        topic_tags=state.topic_tags,
        risk_level=state.risk_level,
        response_provider="template",
        response_mode=state.response_mode,
        support_metadata={"response_goal": strategy.response_goal},
        insight_features=extract_insight_features(state),
    )


def test_support_strategy_handles_interpersonal_tension() -> None:
    state = _build_state(
        primary_emotion="anxiety",
        secondary_emotions=["overwhelm", "sadness"],
        valence_score=-0.57,
        energy_score=0.62,
        stress_score=0.79,
        confidence=0.69,
        response_mode="validating_gentle",
        social_context="friendship",
        event_type="conflict_or_disappointment",
        concern_target="friend",
        relationship_concern=True,
        other_person_state_mentioned=True,
        evidence_spans=["friend", "angry", "didn't finish the deadline on time"],
        topic_tags=["friends", "work/school"],
    )

    strategy = select_support_strategy(state)

    assert state.event_type == "conflict_or_disappointment"
    assert strategy.strategy_type == "validating_gentle"
    assert strategy.support_focus == "mixed"


def test_support_strategy_handles_positive_romantic_excitement() -> None:
    state = _build_state(
        primary_emotion="joy",
        secondary_emotions=["gratitude", "neutral"],
        valence_score=0.7,
        energy_score=0.64,
        stress_score=0.13,
        confidence=1.0,
        response_mode="celebratory_warm",
        social_context="romantic_relationship",
        event_type="relief_or_gratitude",
        concern_target="crush",
        relationship_concern=False,
        other_person_state_mentioned=False,
        evidence_spans=["crush", "likes me"],
        topic_tags=["relationships"],
    )

    strategy = select_support_strategy(state)

    assert strategy.strategy_type == "celebratory_warm"
    assert strategy.response_goal == "reinforce_positive_moment"


def test_support_strategy_handles_low_energy_sadness() -> None:
    state = _build_state(
        primary_emotion="sadness",
        secondary_emotions=["neutral"],
        valence_score=-0.58,
        energy_score=0.18,
        stress_score=0.28,
        confidence=0.61,
        response_mode="low_energy_comfort",
        social_context="solo",
        event_type="exhaustion_or_flatness",
        concern_target=None,
        relationship_concern=False,
        other_person_state_mentioned=False,
        evidence_spans=["empty"],
        topic_tags=["daily life"],
    )

    strategy = select_support_strategy(state)

    assert strategy.strategy_type == "low_energy_comfort"
    assert strategy.personalization_tone == "low_stimulation"


def test_weekly_insight_summary_uses_synthetic_records() -> None:
    records = [
        _build_record(
            "en-demo",
            "My friend seems angry because I didn't finish the deadline on time",
            _build_state(
                primary_emotion="anxiety",
                secondary_emotions=["overwhelm"],
                valence_score=-0.57,
                energy_score=0.62,
                stress_score=0.79,
                confidence=0.69,
                response_mode="validating_gentle",
                social_context="friendship",
                event_type="conflict_or_disappointment",
                concern_target="friend",
                relationship_concern=True,
                other_person_state_mentioned=True,
                evidence_spans=["friend", "angry"],
                topic_tags=["friends", "work/school"],
            ),
        ),
        _build_record(
            "en-demo",
            "My crush likes me",
            _build_state(
                primary_emotion="joy",
                secondary_emotions=["gratitude"],
                valence_score=0.7,
                energy_score=0.64,
                stress_score=0.13,
                confidence=1.0,
                response_mode="celebratory_warm",
                social_context="romantic_relationship",
                event_type="relief_or_gratitude",
                concern_target="crush",
                relationship_concern=False,
                other_person_state_mentioned=False,
                evidence_spans=["crush", "likes me"],
                topic_tags=["relationships"],
            ),
        ),
        _build_record(
            "en-demo",
            "I feel weirdly empty today.",
            _build_state(
                primary_emotion="sadness",
                secondary_emotions=["neutral"],
                valence_score=-0.58,
                energy_score=0.18,
                stress_score=0.28,
                confidence=0.61,
                response_mode="low_energy_comfort",
                social_context="solo",
                event_type="exhaustion_or_flatness",
                concern_target=None,
                relationship_concern=False,
                other_person_state_mentioned=False,
                evidence_spans=["empty"],
                topic_tags=["daily life"],
            ),
        ),
    ]

    insight = build_weekly_insight("en-demo", records)

    assert insight.total_checkins == 3
    assert insight.records_considered_for_insight == 3
    assert "conflict_or_disappointment" in insight.common_negative_triggers
    assert "relief_or_gratitude" in insight.common_positive_anchors
    assert insight.recurring_contexts
    assert insight.insight_summary_text
    assert insight.summary


def test_memory_store_and_summary_capture_recurring_work_stress() -> None:
    store = InMemoryEmotionalMemoryStore()
    user_id = "en-demo"
    work_state = _build_state(
        primary_emotion="overwhelm",
        secondary_emotions=["anxiety"],
        valence_score=-0.48,
        energy_score=0.58,
        stress_score=0.78,
        confidence=0.72,
        response_mode="grounding_soft",
        social_context="work_or_school",
        event_type="deadline_pressure",
        concern_target=None,
        relationship_concern=False,
        other_person_state_mentioned=False,
        evidence_spans=["deadlines", "overwhelming"],
        topic_tags=["work/school"],
    )

    store.append(_build_record(user_id, "Work has been overwhelming this week", work_state))
    store.append(_build_record(user_id, "I've had deadlines piling up for days.", work_state))

    records = store.list_recent(user_id)
    summary = build_memory_summary(records)

    assert len(records) == 2
    assert summary.recent_checkin_count == 2
    assert "deadline_pressure" in summary.dominant_negative_patterns
    assert "deadline_pressure" in summary.recurring_triggers
    assert "work_or_school" in summary.recurring_social_contexts
    assert summary.pattern_detected is True


def test_memory_summary_captures_repeated_relationship_tension() -> None:
    records = [
        _build_record(
            "en-demo",
            "My friend seems angry because I didn't finish the deadline on time",
            _build_state(
                primary_emotion="anxiety",
                secondary_emotions=["overwhelm"],
                valence_score=-0.57,
                energy_score=0.62,
                stress_score=0.79,
                confidence=0.69,
                response_mode="validating_gentle",
                social_context="friendship",
                event_type="conflict_or_disappointment",
                concern_target="friend",
                relationship_concern=True,
                other_person_state_mentioned=True,
                evidence_spans=["friend", "angry"],
                topic_tags=["friends", "work/school"],
            ),
        ),
        _build_record(
            "en-demo",
            "I let my teammate down and I keep replaying it.",
            _build_state(
                primary_emotion="overwhelm",
                secondary_emotions=["sadness"],
                valence_score=-0.5,
                energy_score=0.45,
                stress_score=0.7,
                confidence=0.67,
                response_mode="validating_gentle",
                social_context="work_or_school",
                event_type="conflict_or_disappointment",
                concern_target="teammate",
                relationship_concern=False,
                other_person_state_mentioned=False,
                evidence_spans=["let my teammate down"],
                topic_tags=["work/school", "relationships"],
            ),
        ),
    ]

    summary = build_memory_summary(records)

    assert "conflict_or_disappointment" in summary.dominant_negative_patterns
    assert "conflict_or_disappointment" in summary.recurring_triggers
    assert summary.pattern_detected is True


def test_weekly_insight_handles_sparse_data_gently() -> None:
    records = [
        _build_record(
            "en-demo",
            "My crush likes me",
            _build_state(
                primary_emotion="joy",
                secondary_emotions=["gratitude"],
                valence_score=0.7,
                energy_score=0.64,
                stress_score=0.13,
                confidence=1.0,
                response_mode="celebratory_warm",
                social_context="romantic_relationship",
                event_type="relief_or_gratitude",
                concern_target="crush",
                relationship_concern=False,
                other_person_state_mentioned=False,
                evidence_spans=["crush", "likes me"],
                topic_tags=["relationships"],
            ),
        )
    ]

    insight = build_weekly_insight("en-demo", records)

    assert insight.total_checkins == 1
    assert insight.emotional_trend == "insufficient_data"
    assert insight.suggested_reflection_focus is not None
    assert "not much data yet" in insight.summary
