from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import time

from app.core.config import get_settings
from app.services.ai_core.model_registry import (
    ModelSpec,
    get_model_spec,
    list_supported_models,
    selected_audio_model,
    selected_multilingual_model,
    selected_public_model,
)
from app.services.provider_errors import ProviderExecutionError

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class ModelDownloadStatus:
    key: str
    model_name: str
    completed: bool
    snapshot_path: str | None
    incomplete_files: list[str]
    runtime_status: str
    message: str


def _cache_root() -> str | None:
    settings = get_settings()
    return settings.model_cache_dir or settings.hf_home or None


def _model_dir(model_name: str) -> Path | None:
    cache_root = _cache_root()
    if not cache_root:
        return None
    return Path(cache_root) / f"models--{model_name.replace('/', '--')}"


def _incomplete_files(model_name: str) -> list[str]:
    model_dir = _model_dir(model_name)
    if model_dir is None or not model_dir.exists():
        return []
    return sorted(str(path) for path in model_dir.rglob("*.incomplete"))


def get_model_status(model_name: str, key: str = "custom") -> ModelDownloadStatus:
    spec = get_model_spec(model_name)
    model_dir = _model_dir(model_name)
    snapshot_path = None
    if model_dir is not None:
        refs_path = model_dir / "refs" / "main"
        if refs_path.exists():
            revision = refs_path.read_text(encoding="utf-8").strip()
            candidate = model_dir / "snapshots" / revision
            if candidate.exists():
                snapshot_path = str(candidate)
    incomplete_files = _incomplete_files(model_name)
    runtime_status = spec.runtime_status if spec is not None else "unknown"
    message = "already cached" if snapshot_path and not incomplete_files else "not cached"
    return ModelDownloadStatus(
        key=key,
        model_name=model_name,
        completed=snapshot_path is not None and not incomplete_files,
        snapshot_path=snapshot_path,
        incomplete_files=incomplete_files,
        runtime_status=runtime_status,
        message=message,
    )


def _selection_from_config(selection: str) -> list[tuple[str, ModelSpec]]:
    if selection == "vi-public":
        spec = selected_public_model("vi")
        return [("vi-public", spec)] if spec else []
    if selection == "zh-public":
        spec = selected_public_model("zh")
        return [("zh-public", spec)] if spec else []
    if selection == "multilingual":
        spec = selected_multilingual_model()
        return [("multilingual", spec)] if spec else []
    if selection == "audio":
        spec = selected_audio_model()
        return [("audio", spec)] if spec else []
    if selection == "canonical":
        settings = get_settings()
        return [
            ("vi-canonical", ModelSpec(settings.vi_canonical_model_dir, "vi", "text", "local_artifact", "canonical-artifact", "canonical_v1", None, False, "canonical", True, False, "local_artifact", "Local canonical artifact directory")),
            ("zh-canonical", ModelSpec(settings.zh_canonical_model_dir, "zh", "text", "local_artifact", "canonical-artifact", "canonical_v1", None, False, "canonical", True, False, "local_artifact", "Local canonical artifact directory")),
        ]
    return []


def resolve_model_specs(selection: str | None = None, *, respect_config: bool = False) -> list[tuple[str, ModelSpec]]:
    settings = get_settings()
    if respect_config:
        selected = "all" if selection in {None, "all"} else selection
        if selected == "all":
            pairs: list[tuple[str, ModelSpec]] = []
            for key in ("vi-public", "zh-public", "multilingual", "audio", "canonical"):
                pairs.extend(_selection_from_config(key))
            return pairs
        return _selection_from_config(selected)

    resolved = {
        "vi-public": get_model_spec(settings.vi_public_model_name),
        "zh-public": get_model_spec(settings.zh_public_model_name),
        "multilingual": get_model_spec(settings.multilingual_model_name),
        "audio": get_model_spec(settings.audio_emotion_model_name or "SenseVoiceSmall"),
    }
    if selection in {None, "all"}:
        return [(key, spec) for key, spec in resolved.items() if spec is not None]
    if selection == "canonical":
        return _selection_from_config("canonical")
    spec = resolved.get(selection)
    if spec is None:
        raise ValueError(f"Unknown model selection: {selection}")
    return [(selection, spec)]


def download_models(
    model_specs: Iterable[tuple[str, ModelSpec]] | None = None,
    *,
    retries: int = 3,
    sleep_seconds: float = 2.0,
) -> list[ModelDownloadStatus]:
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError("huggingface_hub is required to pre-download models") from exc

    settings = get_settings()
    cache_dir = _cache_root()
    downloaded: list[ModelDownloadStatus] = []
    targets = list(model_specs) if model_specs is not None else resolve_model_specs("all", respect_config=True)

    for key, spec in targets:
        if spec.provider_type == "local_artifact":
            artifact_path = Path(spec.model_name)
            if not artifact_path.is_absolute():
                artifact_path = PROJECT_ROOT.parent / spec.model_name if str(artifact_path).startswith("backend/") else PROJECT_ROOT / artifact_path
            exists = artifact_path.exists()
            downloaded.append(
                ModelDownloadStatus(
                    key=key,
                    model_name=spec.model_name,
                    completed=exists,
                    snapshot_path=str(artifact_path) if exists else None,
                    incomplete_files=[],
                    runtime_status=spec.runtime_status,
                    message="canonical artifact present" if exists else "requires training first",
                )
            )
            continue
        if not spec.direct_inference:
            if spec.runtime_status == "backbone_only":
                message = "supported as fine-tuning backbone only; direct inference is not available"
            elif spec.runtime_status == "runtime_optional":
                message = "registered in config, but this repo has no runtime integration yet"
            else:
                message = "not directly downloadable for inference"
            downloaded.append(
                ModelDownloadStatus(
                    key=key,
                    model_name=spec.model_name,
                    completed=False,
                    snapshot_path=None,
                    incomplete_files=[],
                    runtime_status=spec.runtime_status,
                    message=message,
                )
            )
            continue
        print(f"[download] start key={key} model={spec.model_name}")
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            status_before = get_model_status(spec.model_name, key=key)
            if status_before.completed:
                print(f"[download] already-complete key={key} snapshot={status_before.snapshot_path}")
                downloaded.append(status_before)
                break
            if status_before.incomplete_files:
                print(f"[download] resume key={key} incomplete_files={len(status_before.incomplete_files)}")
            try:
                snapshot_download(
                    repo_id=spec.model_name,
                    cache_dir=cache_dir,
                    token=settings.hf_token or None,
                    resume_download=True,
                    max_workers=1,
                )
                status_after = get_model_status(spec.model_name, key=key)
                status_after.message = "downloaded" if status_after.completed else "incomplete cache state"
                print(
                    f"[download] finished key={key} complete={status_after.completed} "
                    f"incomplete_files={len(status_after.incomplete_files)}"
                )
                downloaded.append(status_after)
                break
            except Exception as exc:
                last_error = exc
                print(f"[download] retry key={key} attempt={attempt}/{retries} error={exc}")
                if attempt < retries:
                    time.sleep(sleep_seconds)
        else:
            raise ProviderExecutionError(
                f"Failed to download model '{spec.model_name}' after {retries} attempts: {last_error}"
            )
    return downloaded


def supported_model_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in list_supported_models():
        rows.append(
            {
                "model_name": spec.model_name,
                "language": spec.language,
                "modality": spec.modality,
                "family": spec.family,
                "provider_type": spec.provider_type,
                "runtime_status": spec.runtime_status,
                "direct_inference": str(spec.direct_inference),
                "notes": spec.notes,
            }
        )
    return rows
