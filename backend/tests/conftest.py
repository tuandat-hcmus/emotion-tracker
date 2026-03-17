from collections.abc import Generator
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base
from app.db.session import get_db
from app.main import app


class TestSettings:
    app_name = "Emotion Voice Backend Test"
    database_url = "sqlite:///./test.db"
    uploads_dir = "uploads"
    emotion_provider = "model_local"
    enable_text_emotion = True
    enable_audio_emotion = False
    hf_home = None
    model_cache_dir = None
    hf_token = None
    text_model_vi = "visolex/phobert-emotion"
    text_model_zh = "Johnson8187/Chinese-Emotion-Small"
    text_model_fallback = "MilaNLProc/xlm-emo-t"
    audio_emotion_provider = "disabled"
    audio_emotion_model_name = None
    ai_device = "cpu"
    ai_batch_size = 4
    use_mock_stt = True
    use_mock_response = True
    openai_api_key = None
    stt_provider = "mock"
    response_provider = "mock"
    openai_text_model = "gpt-4o-mini"
    openai_audio_model = "gpt-4o-mini-transcribe"
    openai_request_timeout_seconds = 30.0
    max_upload_mb = 20
    allowed_audio_extensions = ".wav,.mp3,.m4a,.ogg,.webm"
    jwt_secret_key = "test-secret-key"
    jwt_algorithm = "HS256"
    access_token_expire_minutes = 60
    auth_optional_for_dev = True
    enable_dev_seed_endpoints = False
    db_echo = False
    auto_create_tables_for_dev = True
    backend_cors_origins = ""


@pytest.fixture
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    yield from _build_client(tmp_path, monkeypatch, auth_optional_for_dev=True)


@pytest.fixture
def strict_client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    yield from _build_client(tmp_path, monkeypatch, auth_optional_for_dev=False)


@pytest.fixture
def dev_client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    yield from _build_client(tmp_path, monkeypatch, auth_optional_for_dev=True, enable_dev_seed_endpoints=True)


def _build_client(
    tmp_path,
    monkeypatch,
    auth_optional_for_dev: bool,
    enable_dev_seed_endpoints: bool = False,
) -> Generator[TestClient, None, None]:
    database_path = tmp_path / "test.db"
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    test_settings = TestSettings()
    test_settings.database_url = f"sqlite:///{database_path}"
    test_settings.uploads_dir = str(uploads_dir)
    test_settings.auth_optional_for_dev = auth_optional_for_dev
    test_settings.enable_dev_seed_endpoints = enable_dev_seed_endpoints

    import app.core.config as config_module
    import app.core.security as security_module
    import app.dependencies.auth as auth_dependency_module
    import app.main as main_module
    import app.services.checkin_processing_service as processing_service_module
    import app.services.response_service as response_service_module
    import app.services.storage_service as storage_service_module
    import app.services.stt_service as stt_service_module

    monkeypatch.setattr(config_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(security_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(auth_dependency_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(main_module, "initialize_database", lambda: None)
    monkeypatch.setattr(processing_service_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(response_service_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(storage_service_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(stt_service_module, "get_settings", lambda: test_settings)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.testing_session_local = TestingSessionLocal

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    if hasattr(app.state, "testing_session_local"):
        delattr(app.state, "testing_session_local")


@pytest.fixture
def settings_factory():
    def factory(**overrides):
        settings = TestSettings()
        for key, value in overrides.items():
            setattr(settings, key, value)
        return settings

    return factory
