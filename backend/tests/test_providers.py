from app.services.response_service import (
    MockResponseGeneratorProvider,
    get_response_generator_provider,
)
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError
from app.services.stt_service import MockSpeechToTextProvider, get_stt_provider
from app.services.ai_core.text_emotion_service import infer_text_emotion
from types import SimpleNamespace
import json


def _stub_en_demo_dependencies(monkeypatch, settings_factory, *, gemini_api_key: str | None, ai_render_debug: bool = True):
    import app.services.en_demo_service as en_demo_service_module
    import app.services.companion_core.memory_store as memory_store_module

    memory_store_module._demo_memory_store.clear()

    settings = settings_factory(enable_ai_core_demo=True, ai_core_demo_response_provider="gemini")
    settings.gemini_api_key = gemini_api_key
    settings.ai_render_debug = ai_render_debug
    monkeypatch.setattr(en_demo_service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(en_demo_service_module, "detect_language", lambda _text: "en")
    monkeypatch.setattr(en_demo_service_module, "detect_safety_risk", lambda _text: {"risk_level": "low", "risk_flags": []})
    monkeypatch.setattr(en_demo_service_module, "tag_topics", lambda _text: ["daily life"])
    monkeypatch.setattr(
        en_demo_service_module,
        "build_emotional_memory_record",
        lambda **_kwargs: SimpleNamespace(user_id="en-demo"),
    )
    monkeypatch.setattr(
        en_demo_service_module,
        "get_demo_memory_store",
        lambda: SimpleNamespace(list_recent=lambda user_id, days=7: [], append=lambda record: None),
    )
    monkeypatch.setattr(
        en_demo_service_module,
        "analyze_emotion",
        lambda _text, risk_level, audio_path=None: {
            "language": "en",
            "primary_emotion": "joy",
            "secondary_emotions": ["neutral", "anger"],
            "emotion_label": "joy",
            "valence_score": 0.7,
            "energy_score": 0.64,
            "stress_score": 0.13,
            "confidence": 1.0,
            "provider_name": "SamLowe/roberta-base-go_emotions",
            "response_mode": "celebratory_warm",
        },
    )
    monkeypatch.setattr(
        en_demo_service_module,
        "build_companion_pipeline",
        lambda **_kwargs: SimpleNamespace(
            emotion_analysis={
                "language": "en",
                "primary_emotion": "joy",
                "secondary_emotions": ["gratitude", "neutral"],
                "emotion_label": "bright",
                "valence_score": 0.7,
                "energy_score": 0.64,
                "stress_score": 0.13,
                "confidence": 1.0,
                "provider_name": "SamLowe/roberta-base-go_emotions",
                "response_mode": "celebratory_warm",
            },
            render_context=SimpleNamespace(
                utterance_type="short_personal_update",
                event_type="relief_or_gratitude",
                relationship_target="crush",
                short_event_flag=True,
                evidence_spans=["crush", "likes me"],
                social_context="romantic_relationship",
                concern_target=None,
            ),
            normalized_state=SimpleNamespace(
                language="en",
                primary_emotion="joy",
                secondary_emotions=["gratitude", "neutral"],
                valence=0.7,
                energy=0.64,
                stress=0.13,
                emotion_owner="user",
                social_context="romantic_relationship",
                event_type="relief_or_gratitude",
                concern_target=None,
                uncertainty=0.0,
                confidence=1.0,
                response_mode="celebratory_warm",
                risk_level="low",
            ),
            memory_summary=SimpleNamespace(
                recent_checkin_count=0,
                dominant_negative_patterns=[],
                dominant_positive_patterns=[],
                recurring_triggers=[],
                recurring_social_contexts=[],
                last_seen_emotional_direction="mixed",
                pattern_detected=False,
                model_dump=lambda: {
                    "recent_checkin_count": 0,
                    "dominant_negative_patterns": [],
                    "dominant_positive_patterns": [],
                    "recurring_triggers": [],
                    "recurring_social_contexts": [],
                    "last_seen_emotional_direction": "mixed",
                    "pattern_detected": False,
                },
            ),
            insight_features=SimpleNamespace(
                is_negative_checkin=False,
                is_positive_checkin=True,
                work_trigger=False,
                relationship_strain=False,
                deadline_related=False,
                loneliness_related=False,
                positive_anchor_candidate=True,
                social_support_signal=True,
                high_stress_flag=False,
                model_dump=lambda: {
                    "is_negative_checkin": False,
                    "is_positive_checkin": True,
                    "work_trigger": False,
                    "relationship_strain": False,
                    "deadline_related": False,
                    "loneliness_related": False,
                    "positive_anchor_candidate": True,
                    "social_support_signal": True,
                    "high_stress_flag": False,
                },
            ),
            support_strategy=SimpleNamespace(
                support_focus="user",
                strategy_type="celebratory_warm",
                suggestion_budget="minimal",
                personalization_tone="soft_celebratory",
                response_goal="reinforce_positive_moment",
                rationale=[],
                model_dump=lambda: {
                    "support_focus": "user",
                    "strategy_type": "celebratory_warm",
                    "suggestion_budget": "minimal",
                    "personalization_tone": "soft_celebratory",
                    "response_goal": "reinforce_positive_moment",
                    "rationale": [],
                },
            ),
            response_plan={"quote_allowed": False, "suggestion_allowed": True, "suggestion_style": "savoring"},
        ),
    )
    return en_demo_service_module


def test_mock_stt_provider_selected_by_default(monkeypatch, settings_factory) -> None:
    import app.services.stt_service as stt_service_module

    monkeypatch.setattr(stt_service_module, "get_settings", lambda: settings_factory(stt_provider="mock"))
    provider = get_stt_provider()

    assert isinstance(provider, MockSpeechToTextProvider)


def test_mock_response_provider_selected_by_default(monkeypatch, settings_factory) -> None:
    import app.services.response_service as response_service_module

    monkeypatch.setattr(
        response_service_module,
        "get_settings",
        lambda: settings_factory(response_provider="mock"),
    )
    provider = get_response_generator_provider()

    assert isinstance(provider, MockResponseGeneratorProvider)


def test_gemini_render_retries_transient_503_and_stays_gemini(monkeypatch) -> None:
    import app.services.gemini_render_service as gemini_render_service_module

    class FakeModels:
        def __init__(self) -> None:
            self.calls = 0

        def generate_content(self, **_kwargs):
            self.calls += 1
            if self.calls < 3:
                raise RuntimeError("503 UNAVAILABLE. high demand")
            return SimpleNamespace(
                text=json.dumps(
                    {
                        "empathetic_text": "That sounds heavy right now.",
                        "follow_up_question": None,
                        "suggestion_text": None,
                        "quote_text": None,
                        "composed_text": "That sounds heavy right now.",
                    }
                )
            )

    fake_models = FakeModels()
    service = gemini_render_service_module.GeminiRenderService.__new__(gemini_render_service_module.GeminiRenderService)
    service._client = SimpleNamespace(models=fake_models)
    service._model = "gemini-2.5-flash"
    service._structured_output = True

    monkeypatch.setattr(gemini_render_service_module.time, "sleep", lambda _seconds: None)

    payload = service.render(
        transcript="I feel stressed because work deadlines are piling up.",
        emotion_analysis={"language": "en", "primary_label": "sadness"},
        topic_tags=["work/school"],
        response_plan={"response_variant": "empathy_only"},
        memory_summary=None,
    )

    assert fake_models.calls == 3
    assert payload["debug"]["renderer_selected"] == "gemini"
    assert payload["payload"]["empathetic_text"] == "That sounds heavy right now."


def test_text_emotion_falls_back_cleanly_without_transformers(monkeypatch, settings_factory) -> None:
    import app.services.ai_core.text_emotion_service as text_service_module
    from app.services.ai_core.schemas import TextEmotionResult

    settings = settings_factory(emotion_model_enabled=True)
    monkeypatch.setattr(text_service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        text_service_module,
        "_infer_text_emotion_with_model",
        lambda _text, _language: (_ for _ in ()).throw(RuntimeError("no model runtime")),
    )
    monkeypatch.setattr(
        text_service_module,
        "_infer_text_emotion_with_legacy_fallback",
        lambda _text, language: TextEmotionResult(
            language=language,
            provider_name="heuristic_fallback",
            raw_model_labels=[],
            ranked_emotions=[("sadness", 1.0)],
            confidence=0.4,
            source_metadata={"mode": "legacy_fallback"},
        ),
    )

    result = infer_text_emotion("Mình hơi buồn và mệt.")

    assert result.provider_name == "heuristic_fallback"
    assert result.ranked_emotions


def test_en_demo_uses_gemini_output_when_render_succeeds(monkeypatch, settings_factory) -> None:
    en_demo_service_module = _stub_en_demo_dependencies(monkeypatch, settings_factory, gemini_api_key="test-key")
    monkeypatch.setattr(
        en_demo_service_module,
        "render_supportive_response",
        lambda **_kwargs: {
            "empathetic_response": "That kind of news can make everything feel a little brighter all at once.",
            "gentle_suggestion": "You can let yourself enjoy this moment without having to figure out everything right away.",
            "safety_note": None,
            "provider_name": "gemini",
        },
    )

    payload, debug_payload = en_demo_service_module.build_en_demo_payload_with_debug(text="My crush likes me")

    assert payload.support.provider_name == "gemini"
    assert payload.support.empathetic_response.startswith("That kind of news can make everything feel a little brighter")
    assert payload.ai_core is not None
    assert payload.ai_core.memory_summary is not None
    assert payload.ai_core.insight_features is not None
    assert payload.ai_core.support_strategy.strategy_type == "celebratory_warm"
    assert payload.ai_core.insight_features.is_positive_checkin is True
    assert payload.debug is not None
    assert payload.debug.selected_provider == "gemini"
    assert payload.debug.gemini_call_attempted is True
    assert payload.debug.gemini_call_succeeded is True
    assert payload.debug.fallback_used is False
    assert payload.debug.fallback_reason is None
    assert payload.debug.error_stage is None
    assert payload.debug.response_parse_status == "parsed_json"
    assert payload.debug.validation_error_summary is None
    assert debug_payload is not None
    assert debug_payload["selected_demo_provider"] == "gemini"
    assert debug_payload["request_language"] == "en"
    assert debug_payload["configured_demo_language"] == "en"
    assert debug_payload["gemini_path_entered"] is True
    assert debug_payload["gemini_api_key_detected"] is True
    assert debug_payload["gemini_call_attempted"] is True
    assert debug_payload["gemini_call_succeeded"] is True
    assert debug_payload["gemini_parse_succeeded"] is True
    assert debug_payload["gemini_validation_succeeded"] is True
    assert debug_payload["fallback_triggered"] is False


def test_en_demo_positive_case_fallback_stays_positive_when_gemini_is_unavailable(monkeypatch, settings_factory) -> None:
    en_demo_service_module = _stub_en_demo_dependencies(monkeypatch, settings_factory, gemini_api_key=None)
    monkeypatch.setattr(
        en_demo_service_module,
        "render_supportive_response",
        lambda **_kwargs: (_ for _ in ()).throw(ProviderConfigurationError("Response provider 'gemini' requires GEMINI_API_KEY")),
    )

    payload, debug_payload = en_demo_service_module.build_en_demo_payload_with_debug(text="My crush likes me")

    assert payload.support.provider_name == "template_fallback"
    assert "brighter" in payload.support.empathetic_response
    assert "hard to name cleanly" not in payload.support.empathetic_response
    assert payload.ai_core is not None
    assert payload.ai_core.memory_summary is not None
    assert payload.ai_core.insight_features is not None
    assert payload.debug is not None
    assert payload.debug.selected_provider == "gemini"
    assert payload.debug.gemini_call_attempted is False
    assert payload.debug.gemini_call_succeeded is False
    assert payload.debug.fallback_used is True
    assert payload.debug.fallback_reason == "missing_api_key"
    assert payload.debug.error_stage == "provider_configuration"
    assert payload.debug.response_parse_status == "not_attempted"
    assert payload.debug.validation_error_summary is None
    assert debug_payload is not None
    assert debug_payload["selected_demo_provider"] == "gemini"
    assert debug_payload["request_language"] == "en"
    assert debug_payload["configured_demo_language"] == "en"
    assert debug_payload["gemini_path_entered"] is True
    assert debug_payload["gemini_api_key_detected"] is False
    assert debug_payload["gemini_call_attempted"] is False
    assert debug_payload["gemini_call_succeeded"] is False
    assert debug_payload["gemini_parse_succeeded"] is None
    assert debug_payload["gemini_validation_succeeded"] is None
    assert debug_payload["fallback_triggered"] is True


def test_en_demo_exposes_safe_debug_for_gemini_execution_error(monkeypatch, settings_factory) -> None:
    en_demo_service_module = _stub_en_demo_dependencies(monkeypatch, settings_factory, gemini_api_key="test-key")
    monkeypatch.setattr(
        en_demo_service_module,
        "render_supportive_response",
        lambda **_kwargs: (_ for _ in ()).throw(ProviderExecutionError("Gemini response generation failed: timeout")),
    )

    payload = en_demo_service_module.build_en_demo_payload(text="My crush likes me")

    assert payload.support.provider_name == "template_fallback"
    assert payload.debug is not None
    assert payload.debug.selected_provider == "gemini"
    assert payload.debug.gemini_call_attempted is True
    assert payload.debug.gemini_call_succeeded is False
    assert payload.debug.fallback_used is True
    assert payload.debug.fallback_reason == "provider_execution_error"
    assert payload.debug.error_stage == "provider_execution"
    assert payload.debug.response_parse_status == "not_parsed"
    assert payload.debug.validation_error_summary == "execution_error"


def test_en_demo_exposes_safe_debug_for_gemini_invalid_json(monkeypatch, settings_factory) -> None:
    en_demo_service_module = _stub_en_demo_dependencies(monkeypatch, settings_factory, gemini_api_key="test-key")
    monkeypatch.setattr(
        en_demo_service_module,
        "render_supportive_response",
        lambda **_kwargs: (_ for _ in ()).throw(ProviderExecutionError("Gemini response generation returned invalid JSON")),
    )

    payload = en_demo_service_module.build_en_demo_payload(text="My crush likes me")

    assert payload.support.provider_name == "template_fallback"
    assert payload.debug is not None
    assert payload.debug.selected_provider == "gemini"
    assert payload.debug.gemini_call_attempted is True
    assert payload.debug.gemini_call_succeeded is False
    assert payload.debug.fallback_used is True
    assert payload.debug.fallback_reason == "invalid_json"
    assert payload.debug.error_stage == "response_parse"
    assert payload.debug.response_parse_status == "invalid_json"
    assert payload.debug.validation_error_summary == "invalid_json_response"


def test_en_demo_exposes_safe_debug_for_gemini_schema_validation_failure(monkeypatch, settings_factory) -> None:
    en_demo_service_module = _stub_en_demo_dependencies(monkeypatch, settings_factory, gemini_api_key="test-key")
    monkeypatch.setattr(
        en_demo_service_module,
        "render_supportive_response",
        lambda **_kwargs: (_ for _ in ()).throw(ProviderExecutionError("Gemini response generation returned invalid style")),
    )

    payload = en_demo_service_module.build_en_demo_payload(text="My crush likes me")

    assert payload.support.provider_name == "template_fallback"
    assert payload.debug is not None
    assert payload.debug.selected_provider == "gemini"
    assert payload.debug.gemini_call_attempted is True
    assert payload.debug.gemini_call_succeeded is False
    assert payload.debug.fallback_used is True
    assert payload.debug.fallback_reason == "schema_validation_failed"
    assert payload.debug.error_stage == "schema_validation"
    assert payload.debug.response_parse_status == "parsed_json"
    assert payload.debug.validation_error_summary == "invalid_style"


def test_en_demo_language_normalization_does_not_skip_gemini_path(monkeypatch, settings_factory) -> None:
    import app.services.en_demo_service as en_demo_service_module
    import app.services.companion_core.memory_store as memory_store_module

    memory_store_module._demo_memory_store.clear()

    settings = settings_factory(enable_ai_core_demo=True, ai_core_demo_response_provider="gemini")
    settings.gemini_api_key = "test-key"
    monkeypatch.setattr(en_demo_service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(en_demo_service_module, "detect_language", lambda _text: "da")
    monkeypatch.setattr(en_demo_service_module, "detect_safety_risk", lambda _text: {"risk_level": "low", "risk_flags": []})
    monkeypatch.setattr(en_demo_service_module, "tag_topics", lambda _text: ["daily life"])
    monkeypatch.setattr(
        en_demo_service_module,
        "build_emotional_memory_record",
        lambda **_kwargs: SimpleNamespace(user_id="en-demo"),
    )
    monkeypatch.setattr(
        en_demo_service_module,
        "get_demo_memory_store",
        lambda: SimpleNamespace(list_recent=lambda user_id, days=7: [], append=lambda record: None),
    )
    monkeypatch.setattr(
        en_demo_service_module,
        "analyze_emotion",
        lambda _text, risk_level, audio_path=None: {
            "language": "da",
            "primary_emotion": "joy",
            "secondary_emotions": ["neutral"],
            "emotion_label": "joy",
            "valence_score": 0.7,
            "energy_score": 0.5,
            "stress_score": 0.1,
            "confidence": 0.9,
            "provider_name": "test-model",
            "response_mode": "celebratory_warm",
        },
    )
    monkeypatch.setattr(
        en_demo_service_module,
        "build_companion_pipeline",
        lambda **_kwargs: SimpleNamespace(
            emotion_analysis={
                "language": "en",
                "primary_emotion": "joy",
                "secondary_emotions": ["neutral"],
                "emotion_label": "joy",
                "valence_score": 0.7,
                "energy_score": 0.5,
                "stress_score": 0.1,
                "confidence": 0.9,
                "provider_name": "test-model",
                "response_mode": "celebratory_warm",
            },
            render_context=SimpleNamespace(
                utterance_type="short_personal_update",
                event_type="relief_or_gratitude",
                relationship_target="crush",
                short_event_flag=True,
                evidence_spans=["crush", "likes me"],
                social_context="romantic_relationship",
                concern_target=None,
            ),
            normalized_state=SimpleNamespace(
                language="en",
                primary_emotion="joy",
                secondary_emotions=["neutral"],
                valence=0.7,
                energy=0.5,
                stress=0.1,
                emotion_owner="user",
                social_context="romantic_relationship",
                event_type="relief_or_gratitude",
                concern_target=None,
                uncertainty=0.1,
                confidence=0.9,
                response_mode="celebratory_warm",
                risk_level="low",
            ),
            memory_summary=SimpleNamespace(
                recent_checkin_count=0,
                dominant_negative_patterns=[],
                dominant_positive_patterns=[],
                recurring_triggers=[],
                recurring_social_contexts=[],
                last_seen_emotional_direction="mixed",
                pattern_detected=False,
                model_dump=lambda: {
                    "recent_checkin_count": 0,
                    "dominant_negative_patterns": [],
                    "dominant_positive_patterns": [],
                    "recurring_triggers": [],
                    "recurring_social_contexts": [],
                    "last_seen_emotional_direction": "mixed",
                    "pattern_detected": False,
                },
            ),
            insight_features=SimpleNamespace(
                is_negative_checkin=False,
                is_positive_checkin=True,
                work_trigger=False,
                relationship_strain=False,
                deadline_related=False,
                loneliness_related=False,
                positive_anchor_candidate=True,
                social_support_signal=True,
                high_stress_flag=False,
                model_dump=lambda: {
                    "is_negative_checkin": False,
                    "is_positive_checkin": True,
                    "work_trigger": False,
                    "relationship_strain": False,
                    "deadline_related": False,
                    "loneliness_related": False,
                    "positive_anchor_candidate": True,
                    "social_support_signal": True,
                    "high_stress_flag": False,
                },
            ),
            support_strategy=SimpleNamespace(
                support_focus="user",
                strategy_type="celebratory_warm",
                suggestion_budget="minimal",
                personalization_tone="soft_celebratory",
                response_goal="reinforce_positive_moment",
                rationale=[],
                model_dump=lambda: {
                    "support_focus": "user",
                    "strategy_type": "celebratory_warm",
                    "suggestion_budget": "minimal",
                    "personalization_tone": "soft_celebratory",
                    "response_goal": "reinforce_positive_moment",
                    "rationale": [],
                },
            ),
            response_plan={"quote_allowed": False, "suggestion_allowed": True, "suggestion_style": "savoring"},
        ),
    )
    monkeypatch.setattr(
        en_demo_service_module,
        "render_supportive_response",
        lambda **_kwargs: {
            "empathetic_response": "That kind of news can make everything feel a little brighter all at once.",
            "gentle_suggestion": None,
            "safety_note": None,
            "provider_name": "gemini",
            "debug": {
                "gemini_call_attempted": True,
                "gemini_call_succeeded": True,
                "gemini_parse_succeeded": True,
                "gemini_validation_succeeded": True,
            },
        },
    )

    payload, debug_payload = en_demo_service_module.build_en_demo_payload_with_debug(text="My crush likes me")

    assert payload.language == "en"
    assert payload.support.provider_name == "gemini"
    assert payload.ai_core is not None
    assert payload.ai_core.memory_summary is not None
    assert debug_payload is not None
    assert debug_payload["request_language"] == "en"
    assert debug_payload["gemini_path_entered"] is True


def _make_vi_pipeline_result(
    *,
    emotion_analysis: dict[str, object],
    risk_level: str = "low",
    event_type: str = "uncertain_mixed_state",
    social_context: str = "solo",
    concern_target: str | None = None,
    support_strategy_type: str | None = None,
    positive: bool = False,
    negative: bool = True,
):
    return SimpleNamespace(
        emotion_analysis=emotion_analysis,
        render_context=SimpleNamespace(
            utterance_type="reflective_checkin",
            event_type=event_type,
            relationship_target=None,
            short_event_flag=False,
            evidence_spans=[],
            social_context=social_context,
            concern_target=concern_target,
        ),
        normalized_state=SimpleNamespace(
            language=str(emotion_analysis["language"]),
            primary_emotion=str(emotion_analysis["primary_emotion"]),
            secondary_emotions=[str(item) for item in emotion_analysis["secondary_emotions"]],
            valence=float(emotion_analysis["valence_score"]),
            energy=float(emotion_analysis["energy_score"]),
            stress=float(emotion_analysis["stress_score"]),
            emotion_owner="user",
            social_context=social_context,
            event_type=event_type,
            concern_target=concern_target,
            uncertainty=round(1.0 - float(emotion_analysis["confidence"]), 2),
            confidence=float(emotion_analysis["confidence"]),
            response_mode=str(emotion_analysis["response_mode"]),
            risk_level=risk_level,
        ),
        memory_summary=SimpleNamespace(
            recent_checkin_count=0,
            dominant_negative_patterns=[],
            dominant_positive_patterns=[],
            recurring_triggers=[],
            recurring_social_contexts=[],
            last_seen_emotional_direction="mixed",
            pattern_detected=False,
        ),
        insight_features=SimpleNamespace(
            is_negative_checkin=negative,
            is_positive_checkin=positive,
            work_trigger=False,
            relationship_strain=False,
            deadline_related=False,
            loneliness_related=False,
            positive_anchor_candidate=positive,
            social_support_signal=False,
            high_stress_flag=float(emotion_analysis["stress_score"]) >= 0.6,
        ),
        support_strategy=SimpleNamespace(
            support_focus="user",
            strategy_type=support_strategy_type or str(emotion_analysis["response_mode"]),
            suggestion_budget="minimal",
            personalization_tone="gentle",
            response_goal="feel_heard",
            rationale=[],
        ),
        response_plan={"quote_allowed": False, "suggestion_allowed": True, "suggestion_style": "small_reflective"},
    )


def test_vi_demo_high_stress_uses_safe_support_with_shared_ai_core(monkeypatch, settings_factory) -> None:
    import app.services.vi_demo_service as vi_demo_service_module

    settings = settings_factory(enable_ai_core_demo=True, ai_core_demo_response_provider="template")
    monkeypatch.setattr(vi_demo_service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(vi_demo_service_module, "detect_language", lambda _text: "vi")
    monkeypatch.setattr(vi_demo_service_module, "detect_safety_risk", lambda _text: {"risk_level": "medium", "risk_flags": ["distress"]})
    monkeypatch.setattr(vi_demo_service_module, "tag_topics", lambda _text: ["công việc"])
    monkeypatch.setattr(
        vi_demo_service_module,
        "analyze_emotion",
        lambda _text, risk_level, audio_path=None: {
            "language": "vi",
            "primary_emotion": "overwhelm",
            "secondary_emotions": ["anxiety"],
            "emotion_label": "căng",
            "valence_score": -0.45,
            "energy_score": 0.74,
            "stress_score": 0.82,
            "confidence": 0.78,
            "provider_name": "heuristic_fallback",
            "response_mode": "grounding_soft",
            "dominant_signals": ["overwhelm_load"],
        },
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_companion_pipeline",
        lambda **kwargs: _make_vi_pipeline_result(
            emotion_analysis=kwargs["emotion_analysis"],
            risk_level="medium",
            event_type="deadline_pressure",
            support_strategy_type="safe_support",
        ),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_emotional_memory_record",
        lambda **_kwargs: SimpleNamespace(user_id="vi-demo"),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "get_demo_memory_store",
        lambda: SimpleNamespace(list_recent=lambda user_id, days=7: [], append=lambda record: None),
    )

    payload = vi_demo_service_module.build_vi_demo_payload(text="Mình đang quá tải vì deadline.")

    assert payload.emotion.response_mode == "safe_support"
    assert payload.support.safety_note is not None
    assert payload.ai_core is not None
    assert payload.ai_core.support_strategy.strategy_type == "safe_support"


def test_vi_demo_anger_case_stays_validating(monkeypatch, settings_factory) -> None:
    import app.services.vi_demo_service as vi_demo_service_module

    settings = settings_factory(enable_ai_core_demo=True, ai_core_demo_response_provider="template")
    monkeypatch.setattr(vi_demo_service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(vi_demo_service_module, "detect_language", lambda _text: "vi")
    monkeypatch.setattr(vi_demo_service_module, "detect_safety_risk", lambda _text: {"risk_level": "low", "risk_flags": []})
    monkeypatch.setattr(vi_demo_service_module, "tag_topics", lambda _text: ["công việc"])
    monkeypatch.setattr(
        vi_demo_service_module,
        "analyze_emotion",
        lambda _text, risk_level, audio_path=None: {
            "language": "vi",
            "primary_emotion": "anger",
            "secondary_emotions": ["overwhelm"],
            "emotion_label": "bực bội",
            "valence_score": -0.52,
            "energy_score": 0.66,
            "stress_score": 0.58,
            "confidence": 0.74,
            "provider_name": "heuristic_fallback",
            "response_mode": "validating_gentle",
            "dominant_signals": ["anger_friction"],
        },
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_companion_pipeline",
        lambda **kwargs: _make_vi_pipeline_result(
            emotion_analysis=kwargs["emotion_analysis"],
            event_type="conflict_or_disappointment",
        ),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_emotional_memory_record",
        lambda **_kwargs: SimpleNamespace(user_id="vi-demo"),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "get_demo_memory_store",
        lambda: SimpleNamespace(list_recent=lambda user_id, days=7: [], append=lambda record: None),
    )

    payload = vi_demo_service_module.build_vi_demo_payload(text="Mình rất bực và ức chế vì chuyện này.")

    assert payload.emotion.response_mode == "validating_gentle"
    assert "không hề quá đáng" in payload.support.empathetic_response
    assert payload.ai_core is not None
    assert payload.ai_core.support_strategy.strategy_type == "validating_gentle"


def test_vi_demo_positive_pride_relief_uses_shared_positive_state(monkeypatch, settings_factory) -> None:
    import app.services.vi_demo_service as vi_demo_service_module

    settings = settings_factory(enable_ai_core_demo=True, ai_core_demo_response_provider="template")
    monkeypatch.setattr(vi_demo_service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(vi_demo_service_module, "detect_language", lambda _text: "vi")
    monkeypatch.setattr(vi_demo_service_module, "detect_safety_risk", lambda _text: {"risk_level": "low", "risk_flags": []})
    monkeypatch.setattr(vi_demo_service_module, "tag_topics", lambda _text: ["thành tựu"])
    monkeypatch.setattr(
        vi_demo_service_module,
        "analyze_emotion",
        lambda _text, risk_level, audio_path=None: {
            "language": "vi",
            "primary_emotion": "joy",
            "secondary_emotions": ["gratitude"],
            "emotion_label": "tự hào",
            "valence_score": 0.7,
            "energy_score": 0.54,
            "stress_score": 0.16,
            "confidence": 0.72,
            "provider_name": "heuristic_fallback",
            "response_mode": "celebratory_warm",
            "dominant_signals": ["pride_growth", "relief_release", "positive_affect"],
        },
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_companion_pipeline",
        lambda **kwargs: _make_vi_pipeline_result(
            emotion_analysis=kwargs["emotion_analysis"],
            event_type="relief_or_gratitude",
            positive=True,
            negative=False,
        ),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_emotional_memory_record",
        lambda **_kwargs: SimpleNamespace(user_id="vi-demo"),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "get_demo_memory_store",
        lambda: SimpleNamespace(list_recent=lambda user_id, days=7: [], append=lambda record: None),
    )

    payload = vi_demo_service_module.build_vi_demo_payload(text="Hôm nay mình vừa tự hào vừa nhẹ nhõm.")

    assert payload.emotion.response_mode == "celebratory_warm"
    assert "phần sáng hơn" in payload.support.empathetic_response
    assert payload.ai_core is not None
    assert payload.ai_core.insight_features.is_positive_checkin is True


def test_vi_demo_mixed_state_maps_shared_ai_core_details(monkeypatch, settings_factory) -> None:
    import app.services.vi_demo_service as vi_demo_service_module

    settings = settings_factory(enable_ai_core_demo=True, ai_core_demo_response_provider="template")
    monkeypatch.setattr(vi_demo_service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(vi_demo_service_module, "detect_language", lambda _text: "vi")
    monkeypatch.setattr(vi_demo_service_module, "detect_safety_risk", lambda _text: {"risk_level": "low", "risk_flags": []})
    monkeypatch.setattr(vi_demo_service_module, "tag_topics", lambda _text: ["đời sống"])
    monkeypatch.setattr(
        vi_demo_service_module,
        "analyze_emotion",
        lambda _text, risk_level, audio_path=None: {
            "language": "vi",
            "primary_emotion": "sadness",
            "secondary_emotions": ["joy"],
            "emotion_label": "phức hợp",
            "valence_score": 0.08,
            "energy_score": 0.42,
            "stress_score": 0.28,
            "confidence": 0.41,
            "provider_name": "heuristic_fallback",
            "response_mode": "supportive_reflective",
            "dominant_signals": ["mixed_emotions", "positive_affect"],
        },
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_companion_pipeline",
        lambda **kwargs: _make_vi_pipeline_result(
            emotion_analysis=kwargs["emotion_analysis"],
            event_type="uncertain_mixed_state",
        ),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_emotional_memory_record",
        lambda **_kwargs: SimpleNamespace(user_id="vi-demo"),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "get_demo_memory_store",
        lambda: SimpleNamespace(list_recent=lambda user_id, days=7: [], append=lambda record: None),
    )

    payload = vi_demo_service_module.build_vi_demo_payload(text="Mình vừa nhẹ nhõm nhưng vẫn buồn.")

    assert payload.emotion.response_mode == "supportive_reflective"
    assert "nhiều lớp cảm xúc" in payload.support.empathetic_response
    assert payload.ai_core is not None
    assert payload.ai_core.normalized_state.event_type == "uncertain_mixed_state"


def test_vi_demo_short_event_adjustment_runs_inside_shared_pipeline(monkeypatch, settings_factory) -> None:
    import app.services.vi_demo_service as vi_demo_service_module

    settings = settings_factory(enable_ai_core_demo=True, ai_core_demo_response_provider="template")
    monkeypatch.setattr(vi_demo_service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(vi_demo_service_module, "detect_language", lambda _text: "vi")
    monkeypatch.setattr(vi_demo_service_module, "detect_safety_risk", lambda _text: {"risk_level": "low", "risk_flags": []})
    monkeypatch.setattr(vi_demo_service_module, "tag_topics", lambda _text: ["sức khỏe", "tình cảm"])
    monkeypatch.setattr(
        vi_demo_service_module,
        "analyze_emotion",
        lambda _text, risk_level, audio_path=None: {
            "language": "vi",
            "primary_emotion": "sadness",
            "secondary_emotions": ["neutral"],
            "emotion_label": "nặng nề",
            "valence_score": -0.4,
            "energy_score": 0.22,
            "stress_score": 0.26,
            "social_need_score": 0.12,
            "confidence": 0.52,
            "provider_name": "heuristic_fallback",
            "response_mode": "low_energy_comfort",
            "dominant_signals": ["sadness_weight"],
            "source_metadata": {},
        },
    )

    def _fake_build_companion_pipeline(**kwargs):
        adjusted = kwargs["emotion_postprocessor"](
            dict(kwargs["emotion_analysis"]),
            SimpleNamespace(event_type="uncertain_mixed_state"),
        )
        return _make_vi_pipeline_result(
            emotion_analysis=adjusted,
            event_type="uncertain_mixed_state",
            support_strategy_type="supportive_reflective",
        )

    monkeypatch.setattr(vi_demo_service_module, "build_companion_pipeline", _fake_build_companion_pipeline)
    monkeypatch.setattr(
        vi_demo_service_module,
        "build_emotional_memory_record",
        lambda **_kwargs: SimpleNamespace(user_id="vi-demo"),
    )
    monkeypatch.setattr(
        vi_demo_service_module,
        "get_demo_memory_store",
        lambda: SimpleNamespace(list_recent=lambda user_id, days=7: [], append=lambda record: None),
    )

    payload = vi_demo_service_module.build_vi_demo_payload(text="Người yêu mình bị ốm.")

    assert payload.emotion.primary_emotion == "anxiety"
    assert payload.emotion.emotion_label == "lo lắng"
    assert payload.emotion.provider_name.endswith("vi_demo_short_event_adjustment")
    assert payload.ai_core is not None
    assert payload.ai_core.normalized_state.primary_emotion == "anxiety"
