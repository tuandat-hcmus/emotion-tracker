import json
from datetime import datetime, timezone
from io import BytesIO

from app.main import app
from app.models.journal_entry import JournalEntry
from app.models.processing_attempt import ProcessingAttempt
from app.models.tree_state import TreeState
from app.models.user_preference import UserPreference
from app.models.wrapup_snapshot import WrapupSnapshot
from app.services.checkin_entry_service import serialize_entry
from app.services.ai_core.text_emotion_service import FRONTEND_LABELS


def _register_and_login(client, email: str, password: str = "secret123") -> dict[str, str]:
    register_response = client.post("/v1/auth/register", json={"email": email, "password": password})
    assert register_response.status_code == 201
    login_response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def _upload_entry(client, headers: dict[str, str]) -> str:
    response = client.post(
        "/v1/checkins/upload",
        headers=headers,
        data={"user_id": "ignored", "session_type": "free"},
        files={"file": ("checkin.wav", BytesIO(b"audio"), "audio/wav")},
    )
    assert response.status_code == 201
    return response.json()["entry_id"]


def _assert_canonical_emotion_contract(payload: dict[str, object]) -> None:
    emotion = payload["emotion_analysis"]
    assert emotion["primary_label"] in FRONTEND_LABELS
    assert set(emotion["scores"].keys()) == set(FRONTEND_LABELS)
    assert isinstance(emotion["secondary_labels"], list)
    assert isinstance(emotion["all_labels"], list)
    assert "provider_name" in emotion
    assert "language" in emotion
    assert "response_mode" in emotion
    assert "dominant_signals" in emotion
    assert "context_tags" in emotion
    assert "enrichment_notes" in emotion

    ai_emotion = payload["ai"]["emotion"]
    assert ai_emotion["primary_label"] == emotion["primary_label"]
    assert ai_emotion["secondary_labels"] == emotion["secondary_labels"]
    assert ai_emotion["all_labels"] == emotion["all_labels"]
    assert ai_emotion["scores"] == emotion["scores"]
    assert ai_emotion["language"] == emotion["language"]
    assert ai_emotion["provider_name"] == emotion["provider_name"]
    assert ai_emotion["response_mode"] == emotion["response_mode"]

    ai_state = payload["ai"]["state"]
    assert ai_state["primary_label"] in FRONTEND_LABELS
    assert isinstance(ai_state["secondary_labels"], list)

    response_plan = payload["response_plan"]
    assert "suggestion_family" in response_plan
    assert "response_variant" in response_plan
    assert "response_mode" in response_plan
    assert response_plan["evidence_bound"] is True
    assert response_plan["response_mode"] == emotion["response_mode"]


def test_english_preview_defaults_to_english_language_and_canonical_contract(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-english@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "I am happy now."},
    )

    assert response.status_code == 200
    payload = response.json()
    _assert_canonical_emotion_contract(payload)
    assert payload["emotion_analysis"]["language"] == "en"
    assert payload["ai"]["emotion"]["language"] == "en"
    assert payload["emotion_analysis"]["provider_name"].startswith("local_xlmr")
    assert isinstance(payload["empathetic_response"], str)


def test_greeting_preview_stays_neutral_and_light(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-greeting@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Hello"},
    )

    assert response.status_code == 200
    payload = response.json()
    _assert_canonical_emotion_contract(payload)
    assert payload["emotion_analysis"]["primary_label"] == "neutral"
    assert payload["ai"]["emotion"]["primary_label"] == "neutral"
    assert payload["ai"]["state"]["primary_label"] == "neutral"
    assert payload["response_plan"]["response_variant"] == "empathy_only"
    assert payload["follow_up_question"] is None
    assert payload["gentle_suggestion"] is None


def test_stress_deadline_preview_uses_stress_supportive_path(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-stress@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "I feel stressed and overwhelmed because work deadlines keep piling up and I can't keep up."},
    )

    assert response.status_code == 200
    payload = response.json()
    _assert_canonical_emotion_contract(payload)
    assert payload["emotion_analysis"]["response_mode"] == "stress_supportive"
    assert payload["emotion_analysis"]["stress_score"] >= 0.68
    assert "deadline_pressure" in payload["emotion_analysis"]["dominant_signals"]
    assert payload["response_plan"]["response_variant"] == "empathy_plus_followup"
    assert payload["follow_up_question"] is not None
    assert payload["gentle_suggestion"] is None
    assert payload["ai"]["strategy"]["strategy_type"] == "stress_supportive"
    assert payload["ai"]["memory"]["insight_features"]["high_stress_flag"] is True


def test_positive_preview_preserves_quote_behavior_and_canonical_contract(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-positive@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Today I feel lighter and more grateful because things are finally improving."},
    )

    assert response.status_code == 200
    payload = response.json()
    _assert_canonical_emotion_contract(payload)
    assert payload["emotion_analysis"]["response_mode"] == "celebratory_warm"
    assert payload["quote"] is not None
    assert payload["response_plan"]["response_variant"] == "empathy_plus_quote"


def test_high_risk_preview_uses_safe_template_path(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-highrisk@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "I don't want to live anymore."},
    )

    assert response.status_code == 200
    payload = response.json()
    _assert_canonical_emotion_contract(payload)
    assert payload["risk_level"] == "high"
    assert payload["emotion_analysis"]["response_mode"] == "high_risk_safe"
    assert payload["gentle_suggestion"] is None
    assert payload["follow_up_question"] is None
    assert payload["quote"] is None
    assert payload["ai_response"] == payload["empathetic_response"]


def test_respond_preview_endpoint_returns_current_structured_contract(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-preview@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "I feel a little stressed because of work deadlines, but I'm still trying."},
    )

    assert response.status_code == 200
    payload = response.json()
    _assert_canonical_emotion_contract(payload)
    assert "ai_response" in payload
    assert "risk_level" in payload
    assert "topic_tags" in payload
    assert "empathetic_response" in payload
    assert "follow_up_question" in payload
    assert "quote" in payload
    assert payload["ai"]["risk"]["level"] == payload["risk_level"]
    assert payload["ai"]["topics"]["tags"] == payload["topic_tags"]
    assert payload["ai"]["response"]["composed_text"] == payload["ai_response"]
    assert payload["ai"]["response"]["empathetic_text"] == payload["empathetic_response"]
    assert payload["ai"]["response"]["plan"]["response_mode"] == payload["response_plan"]["response_mode"]


def test_respond_preview_does_not_persist_or_mutate_state(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-nomutate@example.com")
    me_response = strict_client.get("/v1/auth/me", headers=headers)
    user_id = me_response.json()["id"]

    session_factory = app.state.testing_session_local
    before_db = session_factory()
    try:
        before_entries = before_db.query(JournalEntry).filter(JournalEntry.user_id == user_id).count()
        before_attempts = before_db.query(ProcessingAttempt).filter(ProcessingAttempt.user_id == user_id).count()
        before_tree = before_db.query(TreeState).filter(TreeState.user_id == user_id).count()
        before_wrapups = before_db.query(WrapupSnapshot).filter(WrapupSnapshot.user_id == user_id).count()
        before_preferences = before_db.query(UserPreference).filter(UserPreference.user_id == user_id).count()
    finally:
        before_db.close()

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "I'm a bit tense, but still trying to hold my footing."},
    )

    assert response.status_code == 200

    after_db = session_factory()
    try:
        after_entries = after_db.query(JournalEntry).filter(JournalEntry.user_id == user_id).count()
        after_attempts = after_db.query(ProcessingAttempt).filter(ProcessingAttempt.user_id == user_id).count()
        after_tree = after_db.query(TreeState).filter(TreeState.user_id == user_id).count()
        after_wrapups = after_db.query(WrapupSnapshot).filter(WrapupSnapshot.user_id == user_id).count()
        after_preferences = after_db.query(UserPreference).filter(UserPreference.user_id == user_id).count()
    finally:
        after_db.close()

    assert after_entries == before_entries == 0
    assert after_attempts == before_attempts == 0
    assert after_tree == before_tree == 0
    assert after_wrapups == before_wrapups == 0
    assert after_preferences == before_preferences == 0


def test_mock_mode_is_deterministic_for_preview(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-deterministic@example.com")
    request_payload = {"transcript": "I feel sad, but I also want to talk to someone."}

    first_response = strict_client.post("/v1/me/respond-preview", headers=headers, json=request_payload)
    second_response = strict_client.post("/v1/me/respond-preview", headers=headers, json=request_payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()


def test_respond_preview_respects_quote_opt_out(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-preview-noquote@example.com")
    preference_response = strict_client.put(
        "/v1/me/preferences",
        headers=headers,
        json={"quote_opt_in": False},
    )
    assert preference_response.status_code == 200

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Today I feel grateful and lighter."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["response_mode"] == "celebratory_warm"
    assert payload["quote"] is None


def test_processed_checkin_returns_current_contract(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-process@example.com")
    entry_id = _upload_entry(strict_client, headers)

    response = strict_client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=headers,
        json={"override_transcript": "I feel tired and sad, but I'm still trying to keep going."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["entry_id"] == entry_id
    assert payload["status"] == "processed"
    assert payload["ai_response"]
    assert payload["primary_label"] in FRONTEND_LABELS
    assert set(payload["scores"].keys()) == set(FRONTEND_LABELS)
    assert isinstance(payload["topic_tags"], list)
    assert payload["risk_level"] in {"low", "medium", "high"}
    assert "response_mode" in payload
    assert "empathetic_response" in payload
    assert "dominant_signals" in payload
    assert "confidence" in payload
    assert "language" in payload
    assert "source" in payload
    assert "provider_name" in payload
    assert "gentle_suggestion" in payload
    assert "quote_text" in payload
    assert "response_metadata" in payload
    assert payload["ai"]["emotion"]["primary_label"] == payload["primary_label"]
    assert payload["ai"]["risk"]["level"] == payload["risk_level"]
    assert payload["ai"]["topics"]["tags"] == payload["topic_tags"]
    assert payload["ai"]["response"]["composed_text"] == payload["ai_response"]
    assert payload["ai"]["state"]["primary_label"] in FRONTEND_LABELS
    assert payload["ai"]["strategy"]["strategy_type"]
    assert payload["response_metadata"]["response_plan"]["evidence_bound"] is True


def test_serialize_entry_returns_partial_canonical_ai_object_when_shared_metadata_is_missing() -> None:
    entry = JournalEntry(
        user_id="user-1",
        session_type="free",
        audio_path="uploads/example.wav",
        processing_status="processed",
        transcript_text="I feel a little sad.",
        transcript_confidence=1.0,
        ai_response="I can hear some heaviness in what you shared.",
        emotion_label="sadness",
        valence_score=-0.4,
        energy_score=0.2,
        stress_score=0.3,
        social_need_score=0.12,
        emotion_confidence=0.42,
        dominant_signals_text=json.dumps(["sadness_weight"], ensure_ascii=False),
        topic_tags_text=json.dumps(["daily life"], ensure_ascii=False),
        risk_level="low",
        risk_flags_text=json.dumps([], ensure_ascii=False),
        response_mode="low_energy_comfort",
        empathetic_response="I can hear some heaviness in what you shared.",
        gentle_suggestion=None,
        quote_text=None,
        response_metadata_text=json.dumps({"quote": None}, ensure_ascii=False),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    payload = serialize_entry(entry)

    assert "ai" in payload
    assert payload["ai"]["emotion"]["primary_label"] == "sadness"
    assert payload["ai"]["risk"]["level"] == "low"
    assert payload["ai"]["topics"]["tags"] == ["daily life"]
    assert payload["ai"]["response"]["composed_text"] == entry.ai_response
    assert payload["ai"]["state"]["primary_label"] == "sadness"
    assert payload["ai"]["strategy"]["strategy_type"] is None


def test_high_risk_processed_checkin_suppresses_suggestion_and_quote(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-highrisk-process@example.com")
    entry_id = _upload_entry(strict_client, headers)

    response = strict_client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=headers,
        json={"override_transcript": "I don't want to live anymore."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "high"
    assert payload["response_mode"] == "high_risk_safe"
    assert payload["gentle_suggestion"] is None
    assert payload["quote_text"] is None
    assert payload["empathetic_response"]
    assert payload["response_metadata"]["quote"] is None
    assert payload["ai_response"] == payload["empathetic_response"]


def test_positive_preview_includes_quote_when_allowed(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-preview-quote@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Today I feel grateful and relieved because things are finally improving."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["response_mode"] == "celebratory_warm"
    assert payload["quote"] is not None


def test_positive_processed_checkin_includes_quote_when_allowed(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-process-quote@example.com")
    entry_id = _upload_entry(strict_client, headers)

    response = strict_client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=headers,
        json={"override_transcript": "I feel grateful and relieved because today went much better."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_mode"] == "celebratory_warm"
    assert payload["quote_text"] is not None
    assert payload["response_metadata"]["quote"] is not None
