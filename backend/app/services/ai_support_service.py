from app.services.emotion_service import analyze_emotion
from app.services.empathy_service import build_response_plan
from app.services.response_service import generate_supportive_response
from app.services.safety_service import detect_safety_risk
from app.services.topic_service import tag_topics


def build_support_package(
    *,
    transcript: str,
    user_id: str,
    audio_path: str | None = None,
    quote_opt_in: bool = True,
    override_risk_level: str | None = None,
    override_topic_tags: list[str] | None = None,
    recent_trend: dict[str, object] | None = None,
) -> dict[str, object]:
    safety_result = detect_safety_risk(transcript)
    risk_level = override_risk_level or str(safety_result["risk_level"])
    topic_tags = override_topic_tags or tag_topics(transcript)
    emotion_analysis = analyze_emotion(transcript, risk_level=risk_level, audio_path=audio_path)
    response_plan = build_response_plan(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        recent_trend=recent_trend,
    )
    response_payload = generate_supportive_response(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        response_plan=response_plan,
        user_id=user_id,
        quote_opt_in=quote_opt_in,
    )
    return {
        "emotion_analysis": emotion_analysis,
        "topic_tags": topic_tags,
        "risk_level": risk_level,
        "risk_flags": list(safety_result["risk_flags"]),
        "response_plan": response_plan,
        **response_payload,
    }
