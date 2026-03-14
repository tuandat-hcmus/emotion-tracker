from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import configure_cors, create_app


def test_health_live_returns_success(client) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_ready_returns_success_with_test_db(client) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"]["status"] == "ok"


def test_structured_not_found_error_shape(client) -> None:
    response = client.get("/v1/checkins/missing-entry-id")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Journal entry not found"
    assert payload["detail"] == "Journal entry not found"


def test_structured_validation_error_shape(strict_client) -> None:
    response = strict_client.post("/v1/auth/register", json={"email": "bad-email", "password": "secret123"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["details"]


def test_app_still_boots_in_test_mode() -> None:
    app = create_app()
    assert isinstance(app, FastAPI)


def test_cors_configuration_can_be_instantiated_without_breaking(settings_factory) -> None:
    app = FastAPI()
    settings = settings_factory(backend_cors_origins="http://localhost:3000,http://127.0.0.1:5173")
    configure_cors(app, settings)

    with TestClient(app) as client:
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code in {200, 400}
