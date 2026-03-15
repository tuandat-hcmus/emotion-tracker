from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.journal_entry import JournalEntry
from app.models.wrapup_snapshot import WrapupSnapshot
from app.services.auth_service import authenticate_user
from app.services.demo_seed_service import DEFAULT_DEMO_EMAIL, DEFAULT_DEMO_PASSWORD, reset_demo_data, seed_demo_data


def _login(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_seed_demo_data_service_creates_useful_data(tmp_path) -> None:
    database_path = tmp_path / "seed-service.db"
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        result = seed_demo_data(db, days=30)

        assert result.email == DEFAULT_DEMO_EMAIL
        assert result.entry_count > 0
        assert authenticate_user(db, DEFAULT_DEMO_EMAIL, DEFAULT_DEMO_PASSWORD) is not None
        assert db.query(JournalEntry).filter(JournalEntry.user_id == result.user_id).count() == result.entry_count
        assert db.query(WrapupSnapshot).filter(WrapupSnapshot.user_id == result.user_id).count() >= 1

        removed = reset_demo_data(db, DEFAULT_DEMO_EMAIL)
        assert removed is True
    finally:
        db.close()


def test_dev_seed_endpoint_unavailable_when_disabled(strict_client) -> None:
    response = strict_client.post("/v1/dev/seed-demo-data", json={})

    assert response.status_code == 404


def test_dev_seed_endpoint_when_enabled_populates_manual_flows(dev_client) -> None:
    seed_response = dev_client.post("/v1/dev/seed-demo-data", json={"days": 30})

    assert seed_response.status_code == 200
    seed_payload = seed_response.json()
    assert seed_payload["entry_count"] > 0

    headers = _login(dev_client, DEFAULT_DEMO_EMAIL, DEFAULT_DEMO_PASSWORD)
    home_response = dev_client.get("/v1/me/home", headers=headers)
    calendar_response = dev_client.get("/v1/me/calendar?days=30", headers=headers)

    assert home_response.status_code == 200
    assert calendar_response.status_code == 200
    assert home_response.json()["today"]["total_entries_today"] >= 1
    assert len(calendar_response.json()["items"]) == 30
    assert any(item["entry_count"] > 0 for item in calendar_response.json()["items"])


def test_dev_reset_endpoint_removes_demo_user(dev_client) -> None:
    dev_client.post("/v1/dev/seed-demo-data", json={"days": 14})

    reset_response = dev_client.post("/v1/dev/reset-demo-data", json={"email": DEFAULT_DEMO_EMAIL})

    assert reset_response.status_code == 200
    assert reset_response.json()["removed_user"] is True
