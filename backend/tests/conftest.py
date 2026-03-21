import asyncio
from collections.abc import Generator
from pathlib import Path
import sys

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.ai_core.schemas import TextEmotionResult
from app.services.ai_core.text_emotion_service import FRONTEND_LABELS
from app.services.legacy_emotion_service import infer_legacy_emotion


class TestSettings:
    app_name = "Emotion Voice Backend Test"
    database_url = "sqlite:///./test.db"
    uploads_dir = "uploads"
    emotion_model_enabled = True
    emotion_model_dir = "backend/models/artifacts/emotion_xlmr"
    emotion_model_threshold = None
    emotion_model_device = "cpu"
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


class SyncASGITestClient:
    def __init__(self, app_instance):
        self.app = app_instance

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        transport = httpx.ASGITransport(app=self.app)
        async with self.app.router.lifespan_context(self.app):
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                return await client.request(method, url, **kwargs)

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        return asyncio.run(self._request(method, url, **kwargs))

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)


@pytest.fixture
def client(tmp_path, monkeypatch) -> Generator[SyncASGITestClient, None, None]:
    yield from _build_client(tmp_path, monkeypatch, auth_optional_for_dev=True)


@pytest.fixture
def strict_client(tmp_path, monkeypatch) -> Generator[SyncASGITestClient, None, None]:
    yield from _build_client(tmp_path, monkeypatch, auth_optional_for_dev=False)


@pytest.fixture
def dev_client(tmp_path, monkeypatch) -> Generator[SyncASGITestClient, None, None]:
    yield from _build_client(tmp_path, monkeypatch, auth_optional_for_dev=True, enable_dev_seed_endpoints=True)


def _build_client(
    tmp_path,
    monkeypatch,
    auth_optional_for_dev: bool,
    enable_dev_seed_endpoints: bool = False,
) -> Generator[SyncASGITestClient, None, None]:
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
    import app.services.ai_core.local_emotion_model_service as local_emotion_model_service_module
    import app.services.ai_core.text_emotion_service as text_emotion_service_module
    import app.services.checkin_processing_service as processing_service_module
    import app.services.response_service as response_service_module
    import app.services.storage_service as storage_service_module
    import app.services.stt_service as stt_service_module
    import anyio.to_thread as anyio_to_thread

    monkeypatch.setattr(config_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(security_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(auth_dependency_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(main_module, "initialize_database", lambda: None)
    monkeypatch.setattr(local_emotion_model_service_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(text_emotion_service_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(processing_service_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(response_service_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(storage_service_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(stt_service_module, "get_settings", lambda: test_settings)

    def _infer_local_text_emotion_for_tests(text: str, language: str) -> TextEmotionResult:
        raw = infer_legacy_emotion(text)
        score_map = {label: 0.0 for label in FRONTEND_LABELS}
        remap = {
            "anger": "anger",
            "disgust": "disgust",
            "fear": "fear",
            "anxiety": "fear",
            "overwhelm": "fear",
            "joy": "joy",
            "gratitude": "joy",
            "pride": "joy",
            "relief": "joy",
            "hope": "joy",
            "sadness": "sadness",
            "loneliness": "sadness",
            "emptiness": "sadness",
            "exhaustion": "sadness",
            "surprise": "surprise",
            "neutral": "neutral",
            "calm": "neutral",
        }
        for emotion, score in raw["ranked_emotions"]:
            score_map[remap.get(str(emotion), "neutral")] += float(score)
        ranked_emotions = sorted(
            [(label, round(score_map[label], 4)) for label in FRONTEND_LABELS],
            key=lambda item: item[1],
            reverse=True,
        )
        predicted_labels = [label for label, score in ranked_emotions if score > 0]
        confidence = max(float(raw["confidence"]), max(score_map.values()))
        return TextEmotionResult(
            language=language,
            provider_name="local_xlmr",
            raw_model_labels=predicted_labels,
            ranked_emotions=ranked_emotions,
            confidence=round(confidence, 2),
            source_metadata={
                "mode": "test_local_model_stub",
                "scores": {label: round(score_map[label], 4) for label in FRONTEND_LABELS},
                "predicted_labels": predicted_labels,
                "threshold": None,
                "valence": float(raw["valence"]),
                "energy": float(raw["energy"]),
                "stress": float(raw["stress"]),
            },
        )

    monkeypatch.setattr(text_emotion_service_module, "_infer_text_emotion_with_model", _infer_local_text_emotion_for_tests)

    async def _run_sync_inline(func, *args, abandon_on_cancel=False, cancellable=None, limiter=None):
        del abandon_on_cancel, cancellable, limiter
        return func(*args)

    monkeypatch.setattr(anyio_to_thread, "run_sync", _run_sync_inline)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.testing_session_local = TestingSessionLocal

    yield SyncASGITestClient(app)

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
