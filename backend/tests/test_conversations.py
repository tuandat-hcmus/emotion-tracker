from app.main import app
from app.models.conversation_turn import ConversationTurn
from app.services.conversation_service import process_conversation_turn


def _register_and_login(client, email: str, password: str = "secret123") -> tuple[dict[str, str], str]:
    register_response = client.post("/v1/auth/register", json={"email": email, "password": password})
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]
    login_response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user_id


def test_conversation_session_lifecycle(strict_client) -> None:
    headers, _user_id = _register_and_login(strict_client, "conversation-lifecycle@example.com")

    start_response = strict_client.post("/v1/conversations/sessions", headers=headers)
    assert start_response.status_code == 201
    session_payload = start_response.json()
    assert session_payload["status"] == "active"
    assert session_payload["ended_at"] is None

    end_response = strict_client.post(f"/v1/conversations/sessions/{session_payload['id']}/end", headers=headers)
    assert end_response.status_code == 200
    ended_payload = end_response.json()
    assert ended_payload["status"] == "ended"
    assert ended_payload["ended_at"] is not None


def test_list_conversation_sessions_returns_only_current_user_sessions(strict_client) -> None:
    headers_a, _user_id_a = _register_and_login(strict_client, "conversation-list-a@example.com")
    headers_b, _user_id_b = _register_and_login(strict_client, "conversation-list-b@example.com")

    first_response = strict_client.post("/v1/conversations/sessions", headers=headers_a)
    second_response = strict_client.post("/v1/conversations/sessions", headers=headers_a)
    strict_client.post("/v1/conversations/sessions", headers=headers_b)

    response = strict_client.get("/v1/conversations/sessions?limit=10&offset=0", headers=headers_a)
    assert response.status_code == 200
    payload = response.json()

    assert payload["total"] == 2
    assert payload["limit"] == 10
    assert payload["offset"] == 0
    assert {item["id"] for item in payload["items"]} == {
        first_response.json()["id"],
        second_response.json()["id"],
    }
    assert all(item["user_id"] == payload["user_id"] for item in payload["items"])


def test_get_conversation_session_requires_owner(strict_client) -> None:
    owner_headers, _owner_id = _register_and_login(strict_client, "conversation-owner@example.com")
    other_headers, _other_id = _register_and_login(strict_client, "conversation-other@example.com")

    session_response = strict_client.post("/v1/conversations/sessions", headers=owner_headers)
    session_id = session_response.json()["id"]

    owner_detail = strict_client.get(f"/v1/conversations/sessions/{session_id}", headers=owner_headers)
    assert owner_detail.status_code == 200
    assert owner_detail.json()["id"] == session_id

    forbidden_detail = strict_client.get(
        f"/v1/conversations/sessions/{session_id}",
        headers=other_headers,
    )
    assert forbidden_detail.status_code == 403


def test_get_conversation_session_turns_paginates_and_requires_owner(strict_client) -> None:
    owner_headers, _owner_id = _register_and_login(strict_client, "conversation-turns-owner@example.com")
    other_headers, _other_id = _register_and_login(strict_client, "conversation-turns-other@example.com")
    session_response = strict_client.post("/v1/conversations/sessions", headers=owner_headers)
    session_id = session_response.json()["id"]

    db = app.state.testing_session_local()
    try:
        process_conversation_turn(db, session_id, "The morning felt heavy.")
        process_conversation_turn(db, session_id, "The afternoon felt steadier.")
    finally:
        db.close()

    response = strict_client.get(
        f"/v1/conversations/sessions/{session_id}/turns?limit=2&offset=1",
        headers=owner_headers,
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["session_id"] == session_id
    assert payload["total"] == 4
    assert payload["limit"] == 2
    assert payload["offset"] == 1
    assert len(payload["items"]) == 2
    assert payload["items"][0]["role"] == "assistant"
    assert payload["items"][1]["role"] == "user"

    forbidden_response = strict_client.get(
        f"/v1/conversations/sessions/{session_id}/turns",
        headers=other_headers,
    )
    assert forbidden_response.status_code == 403


def test_process_conversation_turn_persists_user_and_assistant_turns(strict_client) -> None:
    headers, user_id = _register_and_login(strict_client, "conversation-persist@example.com")
    session_response = strict_client.post("/v1/conversations/sessions", headers=headers)
    session_id = session_response.json()["id"]

    db = app.state.testing_session_local()
    try:
        result = process_conversation_turn(db, session_id, "I feel stressed because deadlines are piling up.")
        assert result["session_id"] == session_id
        assert result["assistant_response"]
        assert result["response_plan"]["max_sentences"] == 1
        assert result["response_plan"]["follow_up_question_allowed"] is True

        turns = (
            db.query(ConversationTurn)
            .filter(ConversationTurn.session_id == session_id)
            .order_by(ConversationTurn.created_at.asc(), ConversationTurn.id.asc())
            .all()
        )
        assert len(turns) == 2
        assert turns[0].role == "user"
        assert turns[1].role == "assistant"
        assert turns[0].text == "I feel stressed because deadlines are piling up."
        assert turns[0].emotion_snapshot is not None
        assert turns[0].state_snapshot is not None
        assert turns[1].emotion_snapshot is not None
        assert turns[1].state_snapshot is not None
        assert user_id
    finally:
        db.close()


def test_process_conversation_turn_uses_recent_user_turns_for_context(strict_client, monkeypatch) -> None:
    headers, _user_id = _register_and_login(strict_client, "conversation-context@example.com")
    session_response = strict_client.post("/v1/conversations/sessions", headers=headers)
    session_id = session_response.json()["id"]

    import app.services.conversation_service as conversation_service_module

    captured: dict[str, str] = {}
    original_analyze_emotion = conversation_service_module.analyze_emotion

    def _capture_context(text: str, risk_level: str = "low", audio_path: str | None = None):
        captured["context_text"] = text
        return original_analyze_emotion(text, risk_level=risk_level, audio_path=audio_path)

    monkeypatch.setattr(conversation_service_module, "analyze_emotion", _capture_context)

    db = app.state.testing_session_local()
    try:
        process_conversation_turn(db, session_id, "I feel overwhelmed by work.")
        process_conversation_turn(db, session_id, "The deadlines keep piling up.")
        process_conversation_turn(db, session_id, "I still feel like I cannot catch up.")

        context_text = captured["context_text"]
        assert "I feel overwhelmed by work." in context_text
        assert "The deadlines keep piling up." in context_text
        assert "I still feel like I cannot catch up." in context_text
    finally:
        db.close()


def test_process_conversation_turn_returns_realtime_contract_with_recent_memory(strict_client) -> None:
    headers, _user_id = _register_and_login(strict_client, "conversation-response@example.com")
    session_response = strict_client.post("/v1/conversations/sessions", headers=headers)
    session_id = session_response.json()["id"]

    db = app.state.testing_session_local()
    try:
        process_conversation_turn(db, session_id, "I feel stressed because work deadlines are piling up.")
        result = process_conversation_turn(db, session_id, "It still feels heavy and urgent.")

        assert result["emotion_analysis"]["primary_label"] in {
            "anger",
            "disgust",
            "fear",
            "joy",
            "sadness",
            "surprise",
            "neutral",
        }
        assert result["ai"]["emotion"]["primary_label"] == result["emotion_analysis"]["primary_label"]
        assert result["ai"]["memory"]["recent_checkin_count"] >= 1
        assert result["response_plan"]["response_mode"] == result["emotion_analysis"]["response_mode"]
        assert result["response_plan"]["max_sentences"] == 1
    finally:
        db.close()
