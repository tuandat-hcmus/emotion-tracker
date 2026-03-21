def build_response_plan(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    topic_tags: list[str],
    risk_level: str,
    recent_trend: dict[str, object] | None = None,
) -> dict[str, object]:
    del transcript
    del topic_tags
    del recent_trend

    response_mode = str(emotion_analysis["response_mode"])
    dominant_signals = {str(signal) for signal in emotion_analysis.get("dominant_signals", [])}
    valence_score = float(emotion_analysis["valence_score"])
    energy_score = float(emotion_analysis["energy_score"])
    stress_score = float(emotion_analysis["stress_score"])
    social_need_score = float(emotion_analysis["social_need_score"])
    confidence = float(emotion_analysis["confidence"])

    if risk_level == "high":
        return {
            "opening_style": "steady_presence",
            "acknowledgment_focus": "immediate_distress",
            "suggestion_allowed": False,
            "suggestion_style": "none",
            "quote_allowed": False,
            "avoid_advice": True,
            "tone": "supportive_safe",
            "max_sentences": 2,
        }
    if response_mode == "stress_supportive":
        suggestion_allowed = stress_score < 0.72 and "uncertainty_hedging" not in dominant_signals
        return {
            "opening_style": "pressure_acknowledgment",
            "acknowledgment_focus": "deadline_overload",
            "suggestion_allowed": suggestion_allowed,
            "suggestion_style": "small_grounding" if suggestion_allowed else "none",
            "quote_allowed": False,
            "avoid_advice": False,
            "tone": "steady_grounding",
            "max_sentences": 3,
        }
    if risk_level == "medium" or response_mode == "grounding_soft":
        return {
            "opening_style": "grounding",
            "acknowledgment_focus": "pressure_load" if "overwhelm_load" in dominant_signals else "rising_anxiety",
            "suggestion_allowed": False,
            "suggestion_style": "none",
            "quote_allowed": False,
            "avoid_advice": True,
            "tone": "calm_grounding",
            "max_sentences": 2,
        }
    if response_mode == "celebratory_warm":
        return {
            "opening_style": "warm_reflection" if "gratitude_warmth" not in dominant_signals else "warm_appreciation",
            "acknowledgment_focus": "earned_progress" if "pride_growth" in dominant_signals else "what_is_working",
            "suggestion_allowed": False,
            "suggestion_style": "none",
            "quote_allowed": confidence >= 0.35 and "uncertainty_hedging" not in dominant_signals,
            "avoid_advice": True,
            "tone": "warm_light",
            "max_sentences": 2,
        }
    if response_mode == "low_energy_comfort" or (energy_score <= 0.26 and "mixed_emotions" not in dominant_signals):
        suggestion_allowed = False
        suggestion_style = "none"
        if "loneliness_pull" in dominant_signals and social_need_score >= 0.45 and stress_score < 0.5:
            suggestion_allowed = True
            suggestion_style = "gentle_connection"
        elif "exhaustion_drag" in dominant_signals and stress_score < 0.45:
            suggestion_allowed = True
            suggestion_style = "restful_permission"
        return {
            "opening_style": "soft_presence" if "emptiness_numbness" not in dominant_signals else "quiet_presence",
            "acknowledgment_focus": "lonely_weight" if "loneliness_pull" in dominant_signals else "low_energy_weight",
            "suggestion_allowed": suggestion_allowed,
            "suggestion_style": suggestion_style,
            "quote_allowed": False,
            "avoid_advice": True,
            "tone": "gentle_low_energy",
            "max_sentences": 2,
        }
    if response_mode == "validating_gentle":
        suggestion_allowed = stress_score < 0.5 and "uncertainty_hedging" not in dominant_signals
        suggestion_style = "small_grounding"
        if "loneliness_pull" in dominant_signals and social_need_score >= 0.45 and stress_score < 0.5:
            suggestion_style = "gentle_connection"
        return {
            "opening_style": "gentle_validation" if "anger_friction" not in dominant_signals else "steady_validation",
            "acknowledgment_focus": "friction_strain" if "anger_friction" in dominant_signals else "emotion_weight",
            "suggestion_allowed": suggestion_allowed,
            "suggestion_style": suggestion_style,
            "quote_allowed": False,
            "avoid_advice": True,
            "tone": "gentle_validating",
            "max_sentences": 3,
        }
    suggestion_allowed = confidence >= 0.46 and stress_score < 0.6 and "uncertainty_hedging" not in dominant_signals
    suggestion_style = "small_reflective"
    if social_need_score >= 0.5 and stress_score < 0.5:
        suggestion_style = "gentle_connection"
    if "mixed_emotions" in dominant_signals and valence_score > 0.05 and stress_score < 0.52:
        suggestion_style = "small_reflective"
    return {
        "opening_style": "reflective",
        "acknowledgment_focus": "mixed_state" if "mixed_emotions" in dominant_signals else "emotion_complexity",
        "suggestion_allowed": suggestion_allowed,
        "suggestion_style": suggestion_style,
        "quote_allowed": False,
        "avoid_advice": "mixed_emotions" in dominant_signals or stress_score >= 0.5,
        "tone": "steady_reflective",
        "max_sentences": 3,
    }
