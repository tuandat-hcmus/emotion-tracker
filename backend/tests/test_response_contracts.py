from app.services.response_policy_service import build_follow_up_question
from app.services.response_postcheck_service import postcheck_rendered_response
from app.services.response_service import render_supportive_response


def _sample_emotion(*, language: str = "en", response_mode: str = "supportive_reflective") -> dict[str, object]:
    return {
        "primary_label": "joy" if response_mode == "celebratory_warm" else "fear",
        "secondary_labels": ["neutral"],
        "all_labels": ["joy"] if response_mode == "celebratory_warm" else ["fear"],
        "scores": {
            "anger": 0.01,
            "disgust": 0.0,
            "fear": 0.71 if response_mode != "celebratory_warm" else 0.04,
            "joy": 0.78 if response_mode == "celebratory_warm" else 0.08,
            "sadness": 0.12,
            "surprise": 0.03,
            "neutral": 0.21,
        },
        "threshold": 0.5,
        "confidence": 0.78,
        "provider_name": "local_xlmr+contextual_enrichment",
        "source": "text",
        "language": language,
        "valence_score": 0.42 if response_mode == "celebratory_warm" else -0.33,
        "energy_score": 0.46,
        "stress_score": 0.18 if response_mode == "celebratory_warm" else 0.78,
        "social_need_score": 0.12,
        "response_mode": response_mode,
        "dominant_signals": ["positive_affect"] if response_mode == "celebratory_warm" else ["stress_pressure", "deadline_pressure"],
        "context_tags": ["gratitude"] if response_mode == "celebratory_warm" else ["recurring_trigger_hint"],
        "enrichment_notes": [],
    }


def _sample_plan(*, response_mode: str, risk_level: str = "low") -> dict[str, object]:
    return {
        "opening_style": "warm_appreciation" if response_mode == "celebratory_warm" else "pressure_acknowledgment",
        "acknowledgment_focus": "what_is_working" if response_mode == "celebratory_warm" else "deadline_overload",
        "suggestion_allowed": False if response_mode == "stress_supportive" else True,
        "suggestion_style": "none" if response_mode == "stress_supportive" else "savoring",
        "suggestion_family": None if response_mode == "stress_supportive" else "warm_reinforcement",
        "quote_allowed": response_mode == "celebratory_warm",
        "avoid_advice": response_mode == "celebratory_warm",
        "tone": "warm_light" if response_mode == "celebratory_warm" else "steady_grounding",
        "max_sentences": 2 if response_mode == "celebratory_warm" else 3,
        "follow_up_question_allowed": risk_level == "low" and response_mode == "stress_supportive",
        "response_variant": "empathy_plus_quote" if response_mode == "celebratory_warm" else "empathy_plus_followup",
        "response_mode": response_mode,
        "evidence_bound": True,
        "render_context": {},
        "normalized_state": {},
        "support_strategy": {},
    }


def test_postcheck_repairs_unsupported_specifics() -> None:
    repaired = postcheck_rendered_response(
        rendered={
            "empathetic_text": "It sounds like you missed a deadline and are still carrying conflict from it.",
            "follow_up_question": None,
            "suggestion_text": "Try one slow breath.",
            "quote_text": None,
            "composed_text": "",
        },
        response_plan=_sample_plan(response_mode="stress_supportive"),
        fallback_empathetic_text="It sounds like the pressure is stacking up and landing hard right now.",
        quote_text=None,
        transcript="I feel stressed because work deadlines keep piling up.",
        language="en",
    )

    assert "missed a deadline" not in repaired["empathetic_text"].lower()
    assert "conflict" not in repaired["empathetic_text"].lower()
    assert repaired["follow_up_question"] is not None
    assert repaired["suggestion_text"] is None


def test_render_supportive_response_uses_mock_path_for_low_risk(monkeypatch, settings_factory) -> None:
    import app.services.response_service as response_service_module

    monkeypatch.setattr(
        response_service_module,
        "get_settings",
        lambda: settings_factory(response_provider="mock", use_mock_response=True, response_default_language="en"),
    )

    payload = render_supportive_response(
        transcript="I am happy now.",
        emotion_analysis=_sample_emotion(response_mode="celebratory_warm"),
        topic_tags=["daily life"],
        risk_level="low",
        response_plan=_sample_plan(response_mode="celebratory_warm"),
        user_id="user-1",
        quote_opt_in=False,
    )

    assert payload["provider_name"] == "mock"
    assert isinstance(payload["empathetic_response"], str)
    assert payload["quote"] is None


def test_render_supportive_response_uses_safety_template_for_non_low_risk(monkeypatch, settings_factory) -> None:
    import app.services.response_service as response_service_module

    monkeypatch.setattr(
        response_service_module,
        "get_settings",
        lambda: settings_factory(response_provider="mock", use_mock_response=True, response_default_language="en"),
    )

    payload = render_supportive_response(
        transcript="I don't want to live anymore.",
        emotion_analysis=_sample_emotion(response_mode="high_risk_safe"),
        topic_tags=["daily life"],
        risk_level="high",
        response_plan=_sample_plan(response_mode="high_risk_safe", risk_level="high"),
        user_id="user-1",
        quote_opt_in=True,
    )

    assert payload["provider_name"] == "safety_template"
    assert payload["follow_up_question"] is None
    assert payload["gentle_suggestion"] is None
    assert payload["quote"] is None
    assert payload["ai_response"] == payload["empathetic_response"]


def test_follow_up_question_for_other_person_concern_centers_user_concern() -> None:
    question = build_follow_up_question(
        response_mode="supportive_reflective",
        language="en",
        render_context={"user_stance": "worried_about_other", "event_type": "other_person_distress"},
        normalized_state={"user_stance": "worried_about_other", "event_type": "other_person_distress"},
        support_strategy={"support_focus": "relationship"},
    )

    assert question == "What feels hardest for you about holding this with them right now?"


def test_postcheck_keeps_distinct_follow_up_for_other_person_concern() -> None:
    repaired = postcheck_rendered_response(
        rendered={
            "empathetic_text": "It can be hard to see someone you care about seem that weighed down.",
            "follow_up_question": "What feels hardest for you about holding this with them right now?",
            "suggestion_text": None,
            "quote_text": None,
            "composed_text": "",
        },
        response_plan={
            **_sample_plan(response_mode="supportive_reflective"),
            "response_variant": "empathy_plus_followup",
            "follow_up_question_allowed": True,
            "render_context": {"user_stance": "worried_about_other", "event_type": "other_person_distress"},
            "normalized_state": {"user_stance": "worried_about_other", "event_type": "other_person_distress"},
            "support_strategy": {"support_focus": "relationship"},
        },
        fallback_empathetic_text="It can be hard to hold this kind of worry on your own.",
        quote_text=None,
        transcript="My friend Minh seems sad now.",
        language="en",
    )

    assert repaired["follow_up_question"] == "What feels hardest for you about holding this with them right now?"


def test_postcheck_drops_redundant_suggestion_text() -> None:
    repaired = postcheck_rendered_response(
        rendered={
            "empathetic_text": "The pressure sounds heavy right now, and it makes sense that it feels like a lot.",
            "follow_up_question": None,
            "suggestion_text": "It makes sense that this feels like a lot right now.",
            "quote_text": None,
            "composed_text": "",
        },
        response_plan={
            **_sample_plan(response_mode="grounding_soft"),
            "response_variant": "empathy_plus_suggestion",
            "suggestion_allowed": True,
            "follow_up_question_allowed": False,
        },
        fallback_empathetic_text="The pressure sounds heavy right now.",
        quote_text=None,
        transcript="I can't keep up with all this pressure anymore.",
        language="en",
    )

    assert repaired["suggestion_text"] is None
