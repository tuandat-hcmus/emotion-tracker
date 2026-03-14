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
    assert payload["risk_level"] == "low"
    assert "công việc/học tập" in payload["topic_tags"]


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
    assert payload["items"][0]["entry_id"] == second_entry_id
    assert payload["items"][1]["entry_id"] == first_entry_id


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
    assert payload["items"][0]["entry_id"] == free_entry_id

    offset_response = client.get(
        "/v1/users/history-filter-user/entries",
        params={"limit": 1, "offset": 1},
    )
    assert offset_response.status_code == 200
    assert len(offset_response.json()["items"]) == 1
    assert offset_response.json()["items"][0]["entry_id"] == free_entry_id
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
