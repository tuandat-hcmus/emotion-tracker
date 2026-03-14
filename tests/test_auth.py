from io import BytesIO


def _register_and_login(client, email: str, password: str, display_name: str | None = None) -> dict[str, str]:
    register_payload = {"email": email, "password": password}
    if display_name is not None:
        register_payload["display_name"] = display_name

    register_response = client.post("/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_register_success(strict_client) -> None:
    response = strict_client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "secret123", "display_name": "User"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"


def test_register_duplicate_email(strict_client) -> None:
    strict_client.post("/v1/auth/register", json={"email": "dup@example.com", "password": "secret123"})
    response = strict_client.post("/v1/auth/register", json={"email": "dup@example.com", "password": "secret123"})

    assert response.status_code == 409


def test_login_success(strict_client) -> None:
    strict_client.post("/v1/auth/register", json={"email": "login@example.com", "password": "secret123"})
    response = strict_client.post("/v1/auth/login", json={"email": "login@example.com", "password": "secret123"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_login_invalid_credentials(strict_client) -> None:
    strict_client.post("/v1/auth/register", json={"email": "badlogin@example.com", "password": "secret123"})
    response = strict_client.post("/v1/auth/login", json={"email": "badlogin@example.com", "password": "wrong"})

    assert response.status_code == 401


def test_auth_me_with_valid_token(strict_client) -> None:
    headers = _register_and_login(strict_client, "me@example.com", "secret123")
    response = strict_client.get("/v1/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_me_and_preferences_endpoints(strict_client) -> None:
    headers = _register_and_login(strict_client, "profile@example.com", "secret123", "Profile Name")

    me_response = strict_client.get("/v1/me", headers=headers)
    preferences_response = strict_client.get("/v1/me/preferences", headers=headers)

    assert me_response.status_code == 200
    assert me_response.json()["display_name"] == "Profile Name"
    assert preferences_response.status_code == 200
    assert preferences_response.json()["locale"] == "vi"


def test_preferences_create_update(strict_client) -> None:
    headers = _register_and_login(strict_client, "prefs@example.com", "secret123")
    response = strict_client.put(
        "/v1/me/preferences",
        headers=headers,
        json={
            "locale": "en",
            "timezone": "UTC",
            "quote_opt_in": False,
            "reminder_enabled": True,
            "reminder_time": "08:30",
            "preferred_tree_type": "oak",
            "checkin_goal_per_day": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["locale"] == "en"
    assert payload["reminder_time"] == "08:30"


def test_protected_route_access_with_matching_owner(strict_client) -> None:
    headers = _register_and_login(strict_client, "owner@example.com", "secret123")
    me_response = strict_client.get("/v1/auth/me", headers=headers)
    user_id = me_response.json()["id"]

    upload_response = strict_client.post(
        "/v1/checkins/upload",
        headers=headers,
        data={"user_id": "ignored-user-id", "session_type": "free"},
        files={"file": ("checkin.wav", BytesIO(b"audio"), "audio/wav")},
    )
    entry_id = upload_response.json()["entry_id"]
    strict_client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=headers,
        json={"override_transcript": "Hôm nay mình ổn."},
    )

    entries_response = strict_client.get(f"/v1/users/{user_id}/entries", headers=headers)

    assert entries_response.status_code == 200
    assert entries_response.json()["items"][0]["entry_id"] == entry_id


def test_protected_route_access_denied_for_non_owner(strict_client) -> None:
    owner_headers = _register_and_login(strict_client, "owner2@example.com", "secret123")
    other_headers = _register_and_login(strict_client, "other@example.com", "secret123")
    owner_id = strict_client.get("/v1/auth/me", headers=owner_headers).json()["id"]
    entry_id = strict_client.post(
        "/v1/checkins/upload",
        headers=owner_headers,
        data={"user_id": "ignored-user-id", "session_type": "free"},
        files={"file": ("checkin.wav", BytesIO(b"audio"), "audio/wav")},
    ).json()["entry_id"]

    strict_client.post(
        f"/v1/checkins/{entry_id}/process",
        headers=owner_headers,
        json={"override_transcript": "Hôm nay mình ổn."},
    )

    forbidden_entry = strict_client.get(f"/v1/checkins/{entry_id}", headers=other_headers)
    forbidden_user_scope = strict_client.get(f"/v1/users/{owner_id}/entries", headers=other_headers)

    assert forbidden_entry.status_code == 403
    assert forbidden_user_scope.status_code == 403


def test_auth_optional_for_dev_preserves_existing_no_token_flow(client) -> None:
    response = client.post(
        "/v1/checkins/upload",
        data={"user_id": "dev-user", "session_type": "free"},
        files={"file": ("checkin.wav", BytesIO(b"audio"), "audio/wav")},
    )

    assert response.status_code == 201


def test_authenticated_upload_ignores_form_user_id(strict_client) -> None:
    headers = _register_and_login(strict_client, "uploadowner@example.com", "secret123")
    me_response = strict_client.get("/v1/auth/me", headers=headers)
    user_id = me_response.json()["id"]

    upload_response = strict_client.post(
        "/v1/checkins/upload",
        headers=headers,
        data={"user_id": "different-user", "session_type": "free"},
        files={"file": ("checkin.wav", BytesIO(b"audio"), "audio/wav")},
    )
    entry_id = upload_response.json()["entry_id"]
    entry_response = strict_client.get(f"/v1/checkins/{entry_id}", headers=headers)

    assert entry_response.status_code == 200
    assert entry_response.json()["user_id"] == user_id


def test_crisis_resources_endpoint_shape(client) -> None:
    response = client.get("/v1/resources/crisis?country=US")

    assert response.status_code == 200
    payload = response.json()
    assert payload["country"] == "US"
    assert isinstance(payload["emergency_contacts"], list)
    assert isinstance(payload["crisis_hotlines"], list)
    assert isinstance(payload["notes"], list)
