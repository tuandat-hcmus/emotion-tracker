from io import BytesIO


def _register_and_login(client, email: str, password: str = "secret123", display_name: str | None = None) -> dict[str, str]:
    payload = {"email": email, "password": password}
    if display_name is not None:
        payload["display_name"] = display_name

    register_response = client.post("/v1/auth/register", json=payload)
    assert register_response.status_code == 201
    login_response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def _upload_entry(client, headers: dict[str, str], session_type: str = "free") -> str:
    response = client.post(
        "/v1/checkins/upload",
        headers=headers,
        data={"user_id": "ignored", "session_type": session_type},
        files={"file": ("checkin.wav", BytesIO(b"audio"), "audio/wav")},
    )
    assert response.status_code == 201
    return response.json()["entry_id"]


def _process_entry(client, entry_id: str, headers: dict[str, str], transcript: str) -> None:
    response = client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=headers,
        json={"override_transcript": transcript},
    )
    assert response.status_code == 200


def test_new_me_endpoints_require_auth(strict_client) -> None:
    for path in (
        "/v1/me/home",
        "/v1/me/checkin-status",
        "/v1/me/calendar",
        "/v1/me/wrapups/weekly/latest",
        "/v1/me/wrapups/monthly/latest",
    ):
        response = strict_client.get(path)
        assert response.status_code == 401

    regenerate_response = strict_client.post("/v1/me/wrapups/regenerate", json={"period_type": "week"})
    assert regenerate_response.status_code == 401


def test_home_returns_expected_shape(strict_client) -> None:
    headers = _register_and_login(strict_client, "home@example.com", display_name="Home User")
    entry_id = _upload_entry(strict_client, headers, session_type="morning")
    _process_entry(strict_client, entry_id, headers, "Hôm nay mình bình tĩnh và biết ơn.")

    response = strict_client.get("/v1/me/home", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == "home@example.com"
    assert payload["user"]["display_name"] == "Home User"
    assert payload["preferences_summary"]["quote_opt_in"] is True
    assert payload["today"]["has_morning_checkin"] is True
    assert "total_entries_today" in payload["today"]
    assert "latest_wrapup_meta" in payload
    assert payload["tree"]["vitality_score"] >= 0


def test_home_quote_null_when_opted_out(strict_client) -> None:
    headers = _register_and_login(strict_client, "noquote@example.com")
    preferences_response = strict_client.put(
        "/v1/me/preferences",
        headers=headers,
        json={
            "locale": "en",
            "timezone": "UTC",
            "quote_opt_in": False,
            "reminder_enabled": False,
            "reminder_time": None,
            "preferred_tree_type": "default",
            "checkin_goal_per_day": 1,
        },
    )
    assert preferences_response.status_code == 200

    response = strict_client.get("/v1/me/home", headers=headers)

    assert response.status_code == 200
    assert response.json()["quote"] is None


def test_checkin_status_with_no_entries(strict_client) -> None:
    headers = _register_and_login(strict_client, "empty-status@example.com")

    response = strict_client.get("/v1/me/checkin-status", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_entries"] == 0
    assert payload["session_types_present"] == []
    assert payload["latest_entry_id"] is None
    assert payload["has_morning_checkin"] is False
    assert payload["has_evening_checkin"] is False


def test_checkin_status_detects_morning_and_evening_entries(strict_client) -> None:
    headers = _register_and_login(strict_client, "status-filled@example.com")
    morning_entry_id = _upload_entry(strict_client, headers, session_type="morning")
    evening_entry_id = _upload_entry(strict_client, headers, session_type="evening")

    _process_entry(strict_client, morning_entry_id, headers, "Buổi sáng mình khá ổn.")
    _process_entry(strict_client, evening_entry_id, headers, "Buổi tối mình hơi căng vì deadline.")

    response = strict_client.get("/v1/me/checkin-status", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["has_morning_checkin"] is True
    assert payload["has_evening_checkin"] is True
    assert payload["total_entries"] == 2
    assert payload["session_types_present"] == ["evening", "morning"]
    assert payload["latest_entry_id"] == evening_entry_id


def test_calendar_returns_zero_entry_days(strict_client) -> None:
    headers = _register_and_login(strict_client, "calendar-zero@example.com")
    entry_id = _upload_entry(strict_client, headers)
    _process_entry(strict_client, entry_id, headers, "Hôm nay mình vui và biết ơn.")

    response = strict_client.get("/v1/me/calendar?days=3", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["days"] == 3
    assert len(payload["items"]) == 3
    assert sum(1 for item in payload["items"] if item["entry_count"] == 0) >= 2


def test_calendar_returns_semantic_mood_tokens(strict_client) -> None:
    headers = _register_and_login(strict_client, "calendar-mood@example.com")
    entry_id = _upload_entry(strict_client, headers)
    _process_entry(strict_client, entry_id, headers, "Mình không muốn sống nữa và rất tuyệt vọng.")

    response = strict_client.get("/v1/me/calendar?days=1", headers=headers)

    assert response.status_code == 200
    token = response.json()["items"][0]["mood_color_token"]
    assert token in {"bright", "calm", "neutral", "low", "heavy"}


def test_wrapup_regenerate_creates_and_upserts_snapshot(strict_client) -> None:
    headers = _register_and_login(strict_client, "wrapup-upsert@example.com")
    entry_id = _upload_entry(strict_client, headers)
    _process_entry(strict_client, entry_id, headers, "Hôm nay mình bình tĩnh hơn và biết ơn.")

    first_response = strict_client.post(
        "/v1/me/wrapups/regenerate",
        headers=headers,
        json={"period_type": "week", "anchor_date": "2026-03-13"},
    )
    second_response = strict_client.post(
        "/v1/me/wrapups/regenerate",
        headers=headers,
        json={"period_type": "week", "anchor_date": "2026-03-13"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]
    assert second_response.json()["payload"]["period_type"] == "week"


def test_weekly_latest_returns_snapshot(strict_client) -> None:
    headers = _register_and_login(strict_client, "weekly-latest@example.com")

    response = strict_client.get("/v1/me/wrapups/weekly/latest", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["period_type"] == "week"
    assert payload["payload"]["period_type"] == "week"
    assert "dominant_emotional_patterns" in payload["payload"]
    assert "recurring_triggers" in payload["payload"]
    assert "positive_anchors" in payload["payload"]
    assert "trend_block" in payload["payload"]
    assert "insight_cards" in payload["payload"]


def test_monthly_latest_returns_snapshot(strict_client) -> None:
    headers = _register_and_login(strict_client, "monthly-latest@example.com")

    response = strict_client.get("/v1/me/wrapups/monthly/latest", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["period_type"] == "month"
    assert payload["payload"]["period_type"] == "month"


def test_weekly_wrapup_detects_recurring_deadline_patterns_and_positive_anchors(strict_client) -> None:
    headers = _register_and_login(strict_client, "weekly-patterns@example.com")
    first_entry = _upload_entry(strict_client, headers)
    second_entry = _upload_entry(strict_client, headers)
    third_entry = _upload_entry(strict_client, headers)

    _process_entry(strict_client, first_entry, headers, "I feel stressed because work deadlines keep piling up.")
    _process_entry(strict_client, second_entry, headers, "I still feel overwhelmed and pressured by deadlines at work.")
    _process_entry(strict_client, third_entry, headers, "I feel lighter and grateful because things are improving.")

    response = strict_client.post(
        "/v1/me/wrapups/regenerate",
        headers=headers,
        json={"period_type": "week"},
    )

    assert response.status_code == 200
    payload = response.json()["payload"]
    assert payload["dominant_emotional_patterns"]
    assert "deadline_pressure" in payload["recurring_triggers"]
    assert "deadline_pressure" in payload["workload_deadline_patterns"]
    assert payload["positive_anchors"]
    assert payload["trend_block"]["workload_pattern_detected"] is True
    assert payload["summary_text"]
    assert payload["insight_cards"]


def test_monthly_wrapup_handles_low_data_edge_case(strict_client) -> None:
    headers = _register_and_login(strict_client, "monthly-low-data@example.com")
    entry_id = _upload_entry(strict_client, headers)
    _process_entry(strict_client, entry_id, headers, "I feel calmer today and a bit relieved.")

    response = strict_client.post(
        "/v1/me/wrapups/regenerate",
        headers=headers,
        json={"period_type": "month"},
    )

    assert response.status_code == 200
    payload = response.json()["payload"]
    assert payload["total_entries"] == 1
    assert payload["summary_text"]
    assert isinstance(payload["insight_cards"], list)
    assert payload["trend_block"]["high_stress_frequency"] >= 0.0


def test_wrapup_generation_works_without_any_entries(strict_client) -> None:
    headers = _register_and_login(strict_client, "wrapup-empty@example.com")

    response = strict_client.post("/v1/me/wrapups/regenerate", headers=headers, json={"period_type": "month"})

    assert response.status_code == 200
    payload = response.json()["payload"]
    assert payload["total_entries"] == 0
    assert payload["total_checkin_days"] == 0
    assert payload["dominant_emotional_patterns"] == []
    assert payload["recurring_triggers"] == []
    assert payload["workload_deadline_patterns"] == []
    assert payload["positive_anchors"] == []
    assert payload["high_stress_frequency"] == 0.0
    assert payload["trend_block"]["workload_pattern_detected"] is False
    assert payload["closing_message"]
