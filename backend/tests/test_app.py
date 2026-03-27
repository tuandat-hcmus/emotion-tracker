from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

from app.services.provider_errors import ProviderExecutionError


def _upload_checkin(
    client,
    user_id: str = "demo-user",
    filename: str = "checkin.wav",
    content_type: str = "audio/wav",
    payload: bytes = b"fake-audio",
) -> str:
    response = client.post(
        "/v1/checkins/upload",
        data={"user_id": user_id, "session_type": "free"},
        files={"file": (filename, BytesIO(payload), content_type)},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "uploaded"
    return payload["entry_id"]


def test_health_check(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_checkin(client) -> None:
    entry_id = _upload_checkin(client)
    assert entry_id


def test_upload_checkin_returns_voice_source_type(client) -> None:
    response = client.post(
        "/v1/checkins/upload",
        data={"user_id": "voice-user", "session_type": "free"},
        files={"file": ("checkin.wav", BytesIO(b"fake-audio"), "audio/wav")},
    )

    assert response.status_code == 201
    assert response.json()["source_type"] == "voice"


def test_text_checkin_processes_end_to_end(client) -> None:
    response = client.post(
        "/v1/checkins/text",
        json={
            "user_id": "text-user",
            "session_type": "free",
            "text": "  I feel stressed   because work deadlines are piling up.  ",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "processed"
    assert payload["user_id"] == "text-user"
    assert payload["source_type"] == "text"
    assert payload["audio_path"] is None
    assert payload["transcript_text"] == "I feel stressed because work deadlines are piling up."
    assert payload["transcript_source"] == "user_text"
    assert payload["transcript_provider"] == "text_input"
    assert payload["ai_analysis_complete"] is True
    assert payload["latest_attempt_status"] == "succeeded"
    assert payload["processing_started_at"] is not None
    assert payload["processing_finished_at"] is not None
    assert payload["primary_label"]
    assert payload["response_metadata"]["response_plan"]["response_variant"]
    assert payload["response_metadata"]["source_type"] == "text"
    assert payload["response_metadata"]["transcript_source"] == "user_text"
    assert payload["ai"]["memory"]["recent_checkin_count"] == 0


def test_text_checkin_uses_recent_memory_context(client) -> None:
    first_response = client.post(
        "/v1/checkins/text",
        json={
            "user_id": "text-memory-user",
            "session_type": "free",
            "text": "I feel overwhelmed because the work keeps piling up.",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/v1/checkins/text",
        json={
            "user_id": "text-memory-user",
            "session_type": "free",
            "text": "Today still feels heavy and pressured.",
        },
    )

    assert second_response.status_code == 201
    payload = second_response.json()
    assert payload["ai"]["memory"]["recent_checkin_count"] >= 1
    assert payload["response_metadata"]["memory_summary"]["recent_checkin_count"] >= 1


def test_process_checkin_with_override_transcript(client) -> None:
    entry_id = _upload_checkin(client)

    response = client.post(
        f"/v1/checkins/{entry_id}/process",
        json={"override_transcript": "Hôm nay mình hơi mệt và áp lực vì deadline công việc."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["entry_id"] == entry_id
    assert payload["status"] == "processed"
    assert payload["source_type"] == "voice"
    assert payload["transcript_source"] == "override"
    assert payload["transcript_provider"] == "override"
    assert payload["ai_analysis_complete"] is True
    assert payload["latest_attempt_status"] == "succeeded"
    assert payload["risk_level"] == "low"
    assert "work/school" in payload["topic_tags"]


def test_voice_checkin_processes_via_stt_then_text_pipeline(client, monkeypatch) -> None:
    entry_id = _upload_checkin(client, user_id="voice-pipeline-user")
    import app.services.checkin_processing_service as processing_service_module

    monkeypatch.setattr(
        processing_service_module,
        "transcribe_audio",
        lambda _audio_path: ("  I feel overwhelmed because deadlines are piling up.  ", 0.91),
    )

    response = client.post(f"/v1/checkins/{entry_id}/process", json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "processed"
    assert payload["source_type"] == "voice"
    assert payload["transcript_text"] == "I feel overwhelmed because deadlines are piling up."
    assert payload["transcript_confidence"] == 0.91
    assert payload["transcript_source"] == "stt"
    assert payload["transcript_provider"] in {"mock", "openai", "gemini"}
    assert payload["ai_analysis_complete"] is True
    assert payload["latest_attempt_status"] == "succeeded"
    assert payload["response_metadata"]["normalized_text"] == "I feel overwhelmed because deadlines are piling up."
    assert payload["response_metadata"]["source_type"] == "voice"
    assert payload["response_metadata"]["transcript_source"] == "stt"


def test_high_risk_transcript_uses_safe_message(client) -> None:
    entry_id = _upload_checkin(client, user_id="risk-user")

    response = client.post(
        f"/v1/checkins/{entry_id}/process",
        json={"override_transcript": "Mình không muốn sống nữa và muốn tự tử."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "high"
    assert payload["risk_flags"]
    assert "ưu tiên" in payload["ai_response"]


def test_tree_created_after_processing(client) -> None:
    entry_id = _upload_checkin(client, user_id="tree-user")
    process_response = client.post(
        f"/v1/checkins/{entry_id}/process",
        json={"override_transcript": "Hôm nay mình thấy khá ổn và biết ơn vì công việc tiến triển tốt."},
    )
    assert process_response.status_code == 200

    tree_response = client.get("/v1/users/tree-user/tree")
    assert tree_response.status_code == 200
    tree_payload = tree_response.json()
    assert tree_payload["user_id"] == "tree-user"
    assert tree_payload["vitality_score"] >= 50
    assert tree_payload["current_stage"]


def test_summary_endpoint(client) -> None:
    first_entry_id = _upload_checkin(client, user_id="summary-user")
    second_entry_id = _upload_checkin(client, user_id="summary-user")

    client.post(
        f"/v1/checkins/{first_entry_id}/process",
        json={"override_transcript": "Hôm nay mình vui vì hoàn thành dự án và rất biết ơn."},
    )
    client.post(
        f"/v1/checkins/{second_entry_id}/process",
        json={"override_transcript": "Mình khá căng vì deadline công việc nhưng vẫn đang cố gắng."},
    )

    response = client.get("/v1/users/summary-user/summary?days=30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "summary-user"
    assert payload["days"] == 30
    assert payload["total_entries"] == 2
    assert isinstance(payload["emotion_counts"], dict)
    assert isinstance(payload["risk_counts"], dict)
    assert "dominant_emotional_patterns" in payload
    assert "recurring_triggers" in payload
    assert "workload_deadline_patterns" in payload
    assert "positive_anchors" in payload
    assert "emotional_direction_trend" in payload
    assert "high_stress_frequency" in payload
    assert payload["summary_text"]


def test_summary_endpoint_detects_workload_patterns_and_positive_anchors(client) -> None:
    first_entry_id = _upload_checkin(client, user_id="summary-pattern-user")
    second_entry_id = _upload_checkin(client, user_id="summary-pattern-user")
    third_entry_id = _upload_checkin(client, user_id="summary-pattern-user")

    client.post(
        f"/v1/checkins/{first_entry_id}/process",
        json={"override_transcript": "I feel stressed because work deadlines keep piling up."},
    )
    client.post(
        f"/v1/checkins/{second_entry_id}/process",
        json={"override_transcript": "I still feel overwhelmed by deadlines and pressure at work."},
    )
    client.post(
        f"/v1/checkins/{third_entry_id}/process",
        json={"override_transcript": "Today I feel lighter and grateful because things are improving."},
    )

    response = client.get("/v1/users/summary-pattern-user/summary?days=30")

    assert response.status_code == 200
    payload = response.json()
    assert "deadline_pressure" in payload["recurring_triggers"]
    assert "deadline_pressure" in payload["workload_deadline_patterns"]
    assert payload["positive_anchors"]
    assert payload["high_stress_frequency"] > 0.0
    assert payload["summary_text"]


def test_user_entries_history_endpoint(client) -> None:
    first_entry_id = _upload_checkin(client, user_id="history-user")
    second_entry_id = _upload_checkin(client, user_id="history-user")

    client.post(
        f"/v1/checkins/{first_entry_id}/process",
        json={"override_transcript": "Hôm nay mình ổn và biết ơn gia đình."},
    )
    client.post(
        f"/v1/checkins/{second_entry_id}/process",
        json={"override_transcript": "Mình hơi căng vì deadline công việc."},
    )

    response = client.get("/v1/users/history-user/entries")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "history-user"
    assert payload["total"] == 2
    assert payload["items"][0]["id"] == second_entry_id
    assert payload["items"][0]["entry_id"] == second_entry_id
    assert payload["items"][0]["source_type"] == "voice"
    assert payload["items"][0]["transcript_excerpt"]
    assert payload["items"][0]["primary_label"]
    assert isinstance(payload["items"][0]["secondary_labels"], list)
    assert payload["items"][0]["ai_response_excerpt"]
    assert "transcript_text" not in payload["items"][0]
    assert "ai_response" not in payload["items"][0]
    assert payload["items"][1]["id"] == first_entry_id


def test_user_entries_pagination_and_filters(client) -> None:
    free_entry_id = _upload_checkin(client, user_id="history-filter-user")
    morning_response = client.post(
        "/v1/checkins/upload",
        data={"user_id": "history-filter-user", "session_type": "morning"},
        files={"file": ("morning.wav", BytesIO(b"audio"), "audio/wav")},
    )
    morning_entry_id = morning_response.json()["entry_id"]

    client.post(
        f"/v1/checkins/{free_entry_id}/process",
        json={"override_transcript": "Hôm nay mình khá bình thường."},
    )

    filtered_response = client.get(
        "/v1/users/history-filter-user/entries",
        params={"limit": 1, "offset": 0, "session_type": "free", "status": "processed"},
    )

    assert filtered_response.status_code == 200
    payload = filtered_response.json()
    assert payload["total"] == 1
    assert payload["limit"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == free_entry_id

    offset_response = client.get(
        "/v1/users/history-filter-user/entries",
        params={"limit": 1, "offset": 1},
    )
    assert offset_response.status_code == 200
    assert len(offset_response.json()["items"]) == 1
    assert offset_response.json()["items"][0]["id"] == free_entry_id
    assert morning_entry_id


def test_invalid_upload_extension_rejected(client) -> None:
    response = client.post(
        "/v1/checkins/upload",
        data={"user_id": "demo-user", "session_type": "free"},
        files={"file": ("notes.txt", BytesIO(b"not-audio"), "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported audio file extension" in response.json()["detail"]


def test_oversized_upload_rejected(client, monkeypatch, settings_factory) -> None:
    import app.services.storage_service as storage_service_module

    test_settings = settings_factory(max_upload_mb=1)
    monkeypatch.setattr(storage_service_module, "get_settings", lambda: test_settings)

    response = client.post(
        "/v1/checkins/upload",
        data={"user_id": "demo-user", "session_type": "free"},
        files={"file": ("big.wav", BytesIO(b"a" * (1024 * 1024 + 1)), "audio/wav")},
    )

    assert response.status_code == 400
    assert "exceeds max size" in response.json()["detail"]


def test_process_async_returns_accepted(client) -> None:
    entry_id = _upload_checkin(client, user_id="async-user")

    response = client.post(
        f"/v1/checkins/{entry_id}/process-async",
        json={"override_transcript": "Hôm nay mình khá ổn."},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["entry_id"] == entry_id
    assert payload["status"] == "processing"


def test_attempts_log_created_for_successful_processing(client) -> None:
    entry_id = _upload_checkin(client, user_id="attempt-user")

    client.post(
        f"/v1/checkins/{entry_id}/process",
        json={"override_transcript": "Hôm nay mình khá ổn và biết ơn."},
    )
    attempts_response = client.get(f"/v1/checkins/{entry_id}/attempts")

    assert attempts_response.status_code == 200
    payload = attempts_response.json()
    assert payload["entry_id"] == entry_id
    assert payload["total"] == 1
    assert payload["items"][0]["status"] == "succeeded"
    assert payload["items"][0]["trigger_type"] == "manual"


def test_duplicate_process_call_returns_existing_entry_without_new_attempt(client) -> None:
    entry_id = _upload_checkin(client, user_id="duplicate-user")

    first_response = client.post(
        f"/v1/checkins/{entry_id}/process",
        json={"override_transcript": "I feel overwhelmed because deadlines are piling up."},
    )
    assert first_response.status_code == 200

    second_response = client.post(f"/v1/checkins/{entry_id}/process", json={})
    attempts_response = client.get(f"/v1/checkins/{entry_id}/attempts")

    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert second_payload["entry_id"] == entry_id
    assert second_payload["status"] == "processed"
    assert second_payload["latest_attempt_status"] == "succeeded"
    assert attempts_response.status_code == 200
    assert attempts_response.json()["total"] == 1


def test_failed_processing_leaves_entry_in_coherent_state(client, monkeypatch) -> None:
    import app.services.checkin_processing_service as processing_service_module

    entry_id = _upload_checkin(client, user_id="failure-coherence-user")
    monkeypatch.setattr(
        processing_service_module,
        "transcribe_audio",
        lambda _audio_path: (_ for _ in ()).throw(ProviderExecutionError("pipeline failure for testing")),
    )

    process_response = client.post(f"/v1/checkins/{entry_id}/process", json={})
    detail_response = client.get(f"/v1/checkins/{entry_id}")

    assert process_response.status_code == 502
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["status"] == "failed"
    assert payload["ai_analysis_complete"] is False
    assert payload["latest_attempt_status"] == "failed"
    assert payload["processing_started_at"] is not None
    assert payload["processing_finished_at"] is not None
    assert payload["primary_label"] is None
    assert payload["response_metadata"] is None
    assert payload["ai_response"] is None


def test_attempts_log_created_for_failed_processing(client, monkeypatch) -> None:
    import app.services.checkin_processing_service as processing_service_module

    entry_id = _upload_checkin(client, user_id="attempt-fail-user")
    monkeypatch.setattr(
        processing_service_module,
        "transcribe_audio",
        lambda _audio_path: (_ for _ in ()).throw(ProviderExecutionError("mock provider failure")),
    )

    response = client.post(f"/v1/checkins/{entry_id}/process", json={})
    attempts_response = client.get(f"/v1/checkins/{entry_id}/attempts")

    assert response.status_code == 502
    assert attempts_response.status_code == 200
    payload = attempts_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["status"] == "failed"
    assert "mock provider failure" in payload["items"][0]["error_message"]


def test_reprocess_endpoint_works(client) -> None:
    entry_id = _upload_checkin(client, user_id="reprocess-user")
    client.post(
        f"/v1/checkins/{entry_id}/process",
        json={"override_transcript": "Hôm nay mình hơi mệt."},
    )

    response = client.post(
        f"/v1/checkins/{entry_id}/reprocess",
        json={"override_transcript": "Hôm nay mình vui hơn và biết ơn."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["entry_id"] == entry_id
    assert payload["status"] == "processed"
    assert payload["transcript_text"] == "Hôm nay mình vui hơn và biết ơn."


def test_reprocess_does_not_double_count_tree_state(client) -> None:
    entry_id = _upload_checkin(client, user_id="tree-idempotent-user")
    client.post(
        f"/v1/checkins/{entry_id}/process",
        json={"override_transcript": "Hôm nay mình khá ổn và biết ơn."},
    )
    tree_before = client.get("/v1/users/tree-idempotent-user/tree").json()

    client.post(
        f"/v1/checkins/{entry_id}/reprocess",
        json={"override_transcript": "Hôm nay mình khá ổn và biết ơn."},
    )
    tree_after = client.get("/v1/users/tree-idempotent-user/tree").json()

    assert tree_before["vitality_score"] == tree_after["vitality_score"]
    assert tree_before["streak_days"] == tree_after["streak_days"]


def test_delete_endpoint_removes_db_row_and_audio(client) -> None:
    entry_id = _upload_checkin(client, user_id="delete-user")
    detail_response = client.get(f"/v1/checkins/{entry_id}")
    audio_path = Path(detail_response.json()["audio_path"])
    assert audio_path.exists()

    delete_response = client.delete(f"/v1/checkins/{entry_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True
    assert delete_response.json()["removed_audio"] is True
    assert not audio_path.exists()
    assert client.get(f"/v1/checkins/{entry_id}").status_code == 404


def test_tree_timeline_endpoint_returns_expected_shape(client) -> None:
    first_entry_id = _upload_checkin(client, user_id="timeline-user")
    second_entry_id = _upload_checkin(client, user_id="timeline-user")
    client.post(
        f"/v1/checkins/{first_entry_id}/process",
        json={"override_transcript": "Hôm nay mình vui và biết ơn."},
    )
    client.post(
        f"/v1/checkins/{second_entry_id}/process",
        json={"override_transcript": "Mình hơi căng vì công việc."},
    )

    response = client.get("/v1/users/timeline-user/tree/timeline?days=30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "timeline-user"
    assert payload["days"] == 30
    assert isinstance(payload["items"], list)
    assert payload["items"]
    assert "date" in payload["items"][0]
    assert "vitality_score_after_day" in payload["items"][0]


def test_invalid_state_transitions_return_conflict(client) -> None:
    uploaded_entry_id = _upload_checkin(client, user_id="transition-user")
    processed_entry_id = _upload_checkin(client, user_id="transition-user")
    client.post(
        f"/v1/checkins/{processed_entry_id}/process",
        json={"override_transcript": "Hôm nay mình ổn."},
    )

    reprocess_uploaded = client.post(f"/v1/checkins/{uploaded_entry_id}/reprocess", json={})
    async_processed = client.post(f"/v1/checkins/{processed_entry_id}/process-async", json={})

    assert reprocess_uploaded.status_code == 409
    assert async_processed.status_code == 409


def test_recent_history_endpoint_returns_lightweight_canonical_entries(client) -> None:
    text_response = client.post(
        "/v1/checkins/text",
        json={
            "user_id": "history-canonical-user",
            "session_type": "free",
            "text": "I feel lighter today because work pressure eased a bit.",
        },
    )
    assert text_response.status_code == 201
    voice_entry_id = _upload_checkin(client, user_id="history-canonical-user")
    voice_response = client.post(
        f"/v1/checkins/{voice_entry_id}/process",
        json={"override_transcript": "I still feel pressure because deadlines keep piling up."},
    )
    assert voice_response.status_code == 200

    history_response = client.get("/v1/users/history-canonical-user/entries?limit=5")

    assert history_response.status_code == 200
    payload = history_response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    for item in payload["items"]:
        assert set(item.keys()) == {
            "id",
            "entry_id",
            "status",
            "session_type",
            "source_type",
            "transcript_excerpt",
            "ai_response_excerpt",
            "primary_label",
            "secondary_labels",
            "stress_score",
            "created_at",
            "updated_at",
        }
        assert item["source_type"] in {"text", "voice"}
        assert item["primary_label"] in {"anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"}
        assert isinstance(item["secondary_labels"], list)
