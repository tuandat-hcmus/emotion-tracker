from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class ModelSpec:
    model_name: str
    language: str
    modality: str
    provider_type: str
    task_type: str
    expected_label_space: str
    normalization_adapter: str | None
    cache_required: bool
    family: str
    direct_inference: bool
    fine_tuning_backbone: bool
    runtime_status: str
    notes: str = ""


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "SamLowe/roberta-base-go_emotions": ModelSpec(
        model_name="SamLowe/roberta-base-go_emotions",
        language="en",
        modality="text",
        provider_type="hf_pipeline",
        task_type="text-classification",
        expected_label_space="go_emotions",
        normalization_adapter="go_emotions",
        cache_required=True,
        family="public",
        direct_inference=True,
        fine_tuning_backbone=True,
        runtime_status="direct_classifier",
        notes="Primary English public emotion classifier.",
    ),
    "j-hartmann/emotion-english-distilroberta-base": ModelSpec(
        model_name="j-hartmann/emotion-english-distilroberta-base",
        language="en",
        modality="text",
        provider_type="hf_pipeline",
        task_type="text-classification",
        expected_label_space="hartmann_english",
        normalization_adapter="hartmann_english",
        cache_required=True,
        family="public",
        direct_inference=True,
        fine_tuning_backbone=True,
        runtime_status="direct_classifier",
        notes="Secondary English public emotion classifier.",
    ),
    "j-hartmann/emotion-english-roberta-large": ModelSpec(
        model_name="j-hartmann/emotion-english-roberta-large",
        language="en",
        modality="text",
        provider_type="hf_pipeline",
        task_type="text-classification",
        expected_label_space="hartmann_english",
        normalization_adapter="hartmann_english",
        cache_required=True,
        family="public",
        direct_inference=True,
        fine_tuning_backbone=True,
        runtime_status="direct_classifier",
        notes="Stronger configurable English public classifier.",
    ),
    "visolex/phobert-emotion": ModelSpec(
        model_name="visolex/phobert-emotion",
        language="vi",
        modality="text",
        provider_type="hf_pipeline",
        task_type="text-classification",
        expected_label_space="visolex_phobert_emotion",
        normalization_adapter="visolex_phobert_emotion",
        cache_required=True,
        family="public",
        direct_inference=True,
        fine_tuning_backbone=True,
        runtime_status="direct_classifier",
        notes="Direct Vietnamese emotion classifier. Also usable as a weak-supervision source for canonical training.",
    ),
    "uitnlp/visobert": ModelSpec(
        model_name="uitnlp/visobert",
        language="vi",
        modality="text",
        provider_type="hf_backbone",
        task_type="masked-lm-backbone",
        expected_label_space="backbone_only",
        normalization_adapter=None,
        cache_required=True,
        family="public",
        direct_inference=False,
        fine_tuning_backbone=True,
        runtime_status="backbone_only",
        notes="Backbone-only Vietnamese encoder. Requires a fine-tuned head before direct emotion inference.",
    ),
    "vinai/phobert-large": ModelSpec(
        model_name="vinai/phobert-large",
        language="vi",
        modality="text",
        provider_type="hf_backbone",
        task_type="masked-lm-backbone",
        expected_label_space="backbone_only",
        normalization_adapter=None,
        cache_required=True,
        family="public",
        direct_inference=False,
        fine_tuning_backbone=True,
        runtime_status="backbone_only",
        notes="Backbone-only Vietnamese encoder. Requires fine-tuning for canonical inference.",
    ),
    "Johnson8187/Chinese-Emotion-Small": ModelSpec(
        model_name="Johnson8187/Chinese-Emotion-Small",
        language="zh",
        modality="text",
        provider_type="hf_pipeline",
        task_type="text-classification",
        expected_label_space="johnson_chinese_small",
        normalization_adapter="johnson_chinese_small",
        cache_required=True,
        family="public",
        direct_inference=True,
        fine_tuning_backbone=True,
        runtime_status="direct_classifier",
        notes="Direct Chinese emotion classifier with LABEL_n ids mapped in adapters.",
    ),
    "hfl/chinese-roberta-wwm-ext": ModelSpec(
        model_name="hfl/chinese-roberta-wwm-ext",
        language="zh",
        modality="text",
        provider_type="hf_backbone",
        task_type="masked-lm-backbone",
        expected_label_space="backbone_only",
        normalization_adapter=None,
        cache_required=True,
        family="public",
        direct_inference=False,
        fine_tuning_backbone=True,
        runtime_status="backbone_only",
        notes="Backbone-only Chinese encoder. Requires a fine-tuned classification head.",
    ),
    "Langboat/mengzi-bert-base": ModelSpec(
        model_name="Langboat/mengzi-bert-base",
        language="zh",
        modality="text",
        provider_type="hf_backbone",
        task_type="masked-lm-backbone",
        expected_label_space="backbone_only",
        normalization_adapter=None,
        cache_required=True,
        family="public",
        direct_inference=False,
        fine_tuning_backbone=True,
        runtime_status="backbone_only",
        notes="Backbone-only Chinese encoder. Requires a fine-tuned head for emotion inference.",
    ),
    "MilaNLProc/xlm-emo-t": ModelSpec(
        model_name="MilaNLProc/xlm-emo-t",
        language="multi",
        modality="text",
        provider_type="hf_pipeline",
        task_type="text-classification",
        expected_label_space="xlm_emo_t",
        normalization_adapter="xlm_emo_t",
        cache_required=True,
        family="fallback",
        direct_inference=True,
        fine_tuning_backbone=True,
        runtime_status="direct_classifier",
        notes="Preferred multilingual fallback classifier.",
    ),
    "SenseVoiceSmall": ModelSpec(
        model_name="SenseVoiceSmall",
        language="multi",
        modality="audio",
        provider_type="sensevoice",
        task_type="speech-emotion",
        expected_label_space="audio_provider_specific",
        normalization_adapter=None,
        cache_required=True,
        family="audio",
        direct_inference=False,
        fine_tuning_backbone=False,
        runtime_status="runtime_optional",
        notes="Configurable audio provider placeholder. Not runtime-integrated in this repo yet; processing remains non-blocking.",
    ),
}


def get_model_spec(model_name: str) -> ModelSpec | None:
    return MODEL_REGISTRY.get(model_name)


def list_supported_models() -> list[ModelSpec]:
    return list(MODEL_REGISTRY.values())


def _selected_public_model_name(language: str) -> str:
    settings = get_settings()
    if language == "en":
        return settings.en_public_model_name or settings.text_model_en
    if language == "vi":
        return settings.vi_public_model_name or settings.text_model_vi
    if language == "zh":
        return settings.zh_public_model_name or settings.text_model_zh
    return settings.multilingual_model_name or settings.text_model_fallback


def selected_public_model(language: str) -> ModelSpec | None:
    return get_model_spec(_selected_public_model_name(language))


def selected_multilingual_model() -> ModelSpec | None:
    settings = get_settings()
    return get_model_spec(settings.multilingual_model_name or settings.text_model_fallback)


def selected_audio_model() -> ModelSpec | None:
    settings = get_settings()
    model_name = settings.audio_emotion_model_name or "SenseVoiceSmall"
    return get_model_spec(model_name)


def supported_models_from_config() -> dict[str, list[ModelSpec]]:
    settings = get_settings()
    return {
        "en": [spec for name in settings.split_csv(settings.supported_en_models) if (spec := get_model_spec(name)) is not None],
        "vi": [spec for name in settings.split_csv(settings.supported_vi_models) if (spec := get_model_spec(name)) is not None],
        "zh": [spec for name in settings.split_csv(settings.supported_zh_models) if (spec := get_model_spec(name)) is not None],
        "multilingual": [
            spec for name in settings.split_csv(settings.supported_multilingual_models) if (spec := get_model_spec(name)) is not None
        ],
        "audio": [spec for name in settings.split_csv(settings.supported_audio_models) if (spec := get_model_spec(name)) is not None],
    }
