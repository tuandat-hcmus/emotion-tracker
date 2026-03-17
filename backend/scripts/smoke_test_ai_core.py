import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.core.config import get_settings
from app.models.journal_entry import JournalEntry
from app.models.user_preference import UserPreference
from app.services.ai_core.model_registry import selected_audio_model, selected_multilingual_model, selected_public_model
from app.services.checkin_processing_service import process_entry, serialize_entry
from app.services.emotion_service import analyze_emotion

REPORT_PATH = ROOT / "reports" / "ai_core_smoke_outputs.md"


def _make_db():
    temp_dir = TemporaryDirectory()
    db_path = Path(temp_dir.name) / "smoke.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return temp_dir, session_local


def run_smoke_test() -> dict[str, object]:
    settings = get_settings()
    vi_text = "Hôm nay mình thấy khá nhẹ nhõm và biết ơn vì mọi thứ dần ổn hơn."
    zh_text = "我知道我應該更堅強，但有些時候，這種情緒真的讓我快要崩潰了。"
    normalized = {
        "vi": analyze_emotion(vi_text, risk_level="low"),
        "zh": analyze_emotion(zh_text, risk_level="low"),
    }

    temp_dir, session_local = _make_db()
    try:
        db = session_local()
        db.add(UserPreference(user_id="smoke-user"))
        audio_path = Path(temp_dir.name) / "dummy.wav"
        audio_path.write_bytes(b"not-real-audio")
        entry = JournalEntry(
            user_id="smoke-user",
            session_type="free",
            audio_path=str(audio_path),
            processing_status="uploaded",
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        processed = process_entry(db=db, entry=entry, trigger_type="manual", override_transcript=vi_text)
        mapped = serialize_entry(processed)
        return {
            "selected_config": {
                "enable_canonical_models": settings.enable_canonical_models,
                "enable_public_text_models": settings.enable_public_text_models,
                "enable_audio_emotion": settings.enable_audio_emotion,
                "enable_heuristic_fallback": settings.enable_heuristic_fallback,
                "ai_confidence_threshold": settings.ai_confidence_threshold,
                "ai_low_confidence_hybrid": settings.ai_low_confidence_hybrid,
                "vi_public_model": selected_public_model("vi").model_name if selected_public_model("vi") else None,
                "zh_public_model": selected_public_model("zh").model_name if selected_public_model("zh") else None,
                "multilingual_model": selected_multilingual_model().model_name if selected_multilingual_model() else None,
                "audio_model": selected_audio_model().model_name if selected_audio_model() else None,
                "vi_canonical_dir": settings.vi_canonical_model_dir,
                "zh_canonical_dir": settings.zh_canonical_model_dir,
                "vi_canonical_backbone": settings.vi_canonical_backbone,
                "zh_canonical_backbone": settings.zh_canonical_backbone,
            },
            "normalized_outputs": normalized,
            "processed_checkin": mapped,
        }
    finally:
        db.close()
        temp_dir.cleanup()


def _write_report(payload: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = f"""# AI Core Smoke Outputs

## Selected Config
```json
{json.dumps(payload['selected_config'], ensure_ascii=False, indent=2)}
```

## Vietnamese Normalized Output
```json
{json.dumps(payload['normalized_outputs']['vi'], ensure_ascii=False, indent=2, default=str)}
```

## Chinese Normalized Output
```json
{json.dumps(payload['normalized_outputs']['zh'], ensure_ascii=False, indent=2, default=str)}
```

## Processed Check-In
```json
{json.dumps(payload['processed_checkin'], ensure_ascii=False, indent=2, default=str)}
```
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    payload = run_smoke_test()
    _write_report(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
