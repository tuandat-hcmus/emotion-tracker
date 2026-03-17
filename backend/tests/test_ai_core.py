from io import BytesIO

from app.main import app
from app.models.journal_entry import JournalEntry
from app.models.processing_attempt import ProcessingAttempt
from app.models.tree_state import TreeState
from app.models.user_preference import UserPreference
from app.models.wrapup_snapshot import WrapupSnapshot


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


def test_low_energy_negative_transcript_produces_soft_mode(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-low-energy@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Mình mệt, kiệt sức, không có động lực và thấy buồn."},
    )

    assert response.status_code == 200
    mode = response.json()["emotion_analysis"]["response_mode"]
    assert mode in {"low_energy_comfort", "validating_gentle", "supportive_reflective"}


def test_lonely_withdrawn_transcript_surfaces_connection_signals(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-lonely@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Mấy hôm nay mình chỉ muốn thu mình, không muốn gặp ai và thấy rất cô đơn."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["emotion_label"] in {"cô đơn", "chùng xuống", "nặng nề", "lo lắng"}
    assert payload["emotion_analysis"]["response_mode"] == "low_energy_comfort"
    assert "connection_need" in payload["emotion_analysis"]["dominant_signals"]


def test_overwhelmed_anxious_transcript_uses_grounding_mode(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-overwhelmed@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Mình lo lắng và ngộp vì deadline dồn dập, cảm giác không theo kịp mọi thứ."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["emotion_label"] in {"căng", "lo lắng"}
    assert payload["emotion_analysis"]["response_mode"] == "grounding_soft"
    assert payload["gentle_suggestion"] is None


def test_frustrated_angry_transcript_is_validated_without_flattening(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-angry@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Mình rất bực bội và ức chế vì công việc cứ đổ lên đầu, nghe thật vô lý."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["emotion_label"] in {"bực bội", "căng"}
    assert payload["emotion_analysis"]["response_mode"] == "validating_gentle"
    assert "anger_friction" in payload["emotion_analysis"]["dominant_signals"]


def test_positive_transcript_produces_celebratory_mode(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-positive@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Hôm nay mình rất biết ơn, nhẹ nhõm và thấy mọi thứ tiến triển tốt."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["response_mode"] == "celebratory_warm"
    assert payload["gentle_suggestion"] is None


def test_positive_proud_transcript_is_recognized_as_growth(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-proud@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Hôm nay mình thật sự tự hào vì đã vượt qua được một việc khó và làm được điều mình sợ."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["emotion_label"] == "tự hào"
    assert payload["emotion_analysis"]["response_mode"] == "celebratory_warm"
    assert "pride_growth" in payload["emotion_analysis"]["dominant_signals"]


def test_mixed_emotion_transcript_remains_reflective(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-mixed@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Mình vừa nhẹ nhõm vì xong việc, nhưng vẫn buồn và hơi trống rỗng sau tất cả."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["emotion_label"] == "phức hợp"
    assert payload["emotion_analysis"]["response_mode"] == "supportive_reflective"
    assert "mixed_emotions" in payload["emotion_analysis"]["dominant_signals"]


def test_high_risk_transcript_produces_safe_mode(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-highrisk@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Mình không muốn sống nữa và muốn tự tử."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["response_mode"] == "high_risk_safe"
    assert payload["gentle_suggestion"] is None
    assert payload["quote"] is None
    assert payload["ai_response"] == payload["empathetic_response"]


def test_respond_preview_endpoint_returns_structured_outputs(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-preview@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Mình hơi căng vì deadline công việc nhưng vẫn cố gắng."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "ai_response" in payload
    assert "emotion_analysis" in payload
    assert "emotion_label" in payload["emotion_analysis"]
    assert "risk_level" in payload
    assert "response_plan" in payload
    assert "empathetic_response" in payload
    assert "quote" in payload
    assert isinstance(payload["topic_tags"], list)
    assert "topic_tags" in payload
    assert "social_need_score" in payload["emotion_analysis"]
    assert "confidence" in payload["emotion_analysis"]
    assert "language" in payload["emotion_analysis"]
    assert "primary_emotion" in payload["emotion_analysis"]
    assert "secondary_emotions" in payload["emotion_analysis"]
    assert "source" in payload["emotion_analysis"]
    assert "raw_model_labels" in payload["emotion_analysis"]
    assert "provider_name" in payload["emotion_analysis"]
    assert isinstance(payload["emotion_analysis"]["dominant_signals"], list)
    assert "opening_style" in payload["response_plan"]
    assert "suggestion_allowed" in payload["response_plan"]


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
        json={"transcript": "Mình hơi căng nhưng vẫn đang cố gắng giữ nhịp."},
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
    request_payload = {"transcript": "Mình hơi buồn nhưng cũng muốn nói chuyện với ai đó."}

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
        json={"transcript": "Hôm nay mình rất biết ơn và nhẹ nhõm."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["emotion_analysis"]["response_mode"] == "celebratory_warm"
    assert payload["quote"] is None
    assert "Small signs of steadiness are worth keeping." not in payload["ai_response"]
    assert "Let this calmer moment count as real progress." not in payload["ai_response"]


def test_checkin_process_response_keeps_legacy_fields_and_adds_new_ones(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-process@example.com")
    entry_id = _upload_entry(strict_client, headers)

    response = strict_client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=headers,
        json={"override_transcript": "Hôm nay mình hơi mệt và buồn, nhưng vẫn cố đi tiếp."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["entry_id"] == entry_id
    assert payload["status"] == "processed"
    assert payload["ai_response"]
    assert payload["emotion_label"]
    assert isinstance(payload["topic_tags"], list)
    assert payload["risk_level"] in {"low", "medium", "high"}
    assert "response_mode" in payload
    assert "empathetic_response" in payload
    assert "dominant_signals" in payload
    assert "confidence" in payload
    assert "language" in payload
    assert "primary_emotion" in payload
    assert "secondary_emotions" in payload
    assert "source" in payload
    assert "raw_model_labels" in payload
    assert "provider_name" in payload
    assert "gentle_suggestion" in payload
    assert "quote_text" in payload
    assert "response_metadata" in payload


def test_high_risk_processed_checkin_suppresses_suggestion_and_quote(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-highrisk-process@example.com")
    entry_id = _upload_entry(strict_client, headers)

    response = strict_client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=headers,
        json={"override_transcript": "Mình không muốn sống nữa và muốn tự tử."},
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


def test_processed_checkin_respects_quote_opt_out(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-process-noquote@example.com")
    preference_response = strict_client.put(
        "/v1/me/preferences",
        headers=headers,
        json={"quote_opt_in": False},
    )
    assert preference_response.status_code == 200
    entry_id = _upload_entry(strict_client, headers)

    response = strict_client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=headers,
        json={"override_transcript": "Hôm nay mình rất biết ơn và thấy mọi thứ tiến triển tốt."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_mode"] == "celebratory_warm"
    assert payload["quote_text"] is None
    assert payload["response_metadata"]["quote"] is None


def test_positive_preview_includes_quote_when_allowed(strict_client) -> None:
    headers = _register_and_login(strict_client, "ai-preview-quote@example.com")

    response = strict_client.post(
        "/v1/me/respond-preview",
        headers=headers,
        json={"transcript": "Hôm nay mình biết ơn và nhẹ nhõm vì mọi thứ cuối cùng cũng ổn hơn."},
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
        json={"override_transcript": "Mình biết ơn và nhẹ nhõm vì hôm nay mọi thứ tiến triển tốt hơn nhiều."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_mode"] == "celebratory_warm"
    assert payload["quote_text"] is not None
    assert payload["response_metadata"]["quote"] is not None
