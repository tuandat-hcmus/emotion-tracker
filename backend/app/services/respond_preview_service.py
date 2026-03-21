from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.checkin import (
    AIContractResponse,
    EmotionAnalysisResponse,
    RespondPreviewRequest,
    RespondPreviewResponse,
    ResponsePlanResponse,
    ResponseQuoteResponse,
)
from app.services.ai_contract_service import build_ai_contract
from app.services.ai_support_service import build_support_package


def build_respond_preview_response(
    *,
    db: Session,
    current_user: User,
    payload: RespondPreviewRequest,
) -> RespondPreviewResponse:
    preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).one_or_none()
    support_package = build_support_package(
        transcript=payload.transcript,
        user_id=current_user.id,
        audio_path=None,
        quote_opt_in=preferences.quote_opt_in if preferences is not None else True,
        override_risk_level=payload.override_risk_level,
        override_topic_tags=payload.override_topic_tags,
    )
    quote = support_package["quote"]
    return RespondPreviewResponse(
        emotion_analysis=EmotionAnalysisResponse(
            primary_label=str(support_package["emotion_analysis"]["primary_label"]),
            secondary_labels=list(support_package["emotion_analysis"]["secondary_labels"]),
            all_labels=list(support_package["emotion_analysis"]["all_labels"]),
            scores=dict(support_package["emotion_analysis"]["scores"]),
            threshold=(
                float(support_package["emotion_analysis"]["threshold"])
                if support_package["emotion_analysis"]["threshold"] is not None
                else None
            ),
            valence_score=float(support_package["emotion_analysis"]["valence_score"]),
            energy_score=float(support_package["emotion_analysis"]["energy_score"]),
            stress_score=float(support_package["emotion_analysis"]["stress_score"]),
            social_need_score=float(support_package["emotion_analysis"]["social_need_score"]),
            confidence=float(support_package["emotion_analysis"]["confidence"]),
            dominant_signals=list(support_package["emotion_analysis"]["dominant_signals"]),
            context_tags=list(support_package["emotion_analysis"]["context_tags"]),
            enrichment_notes=list(support_package["emotion_analysis"]["enrichment_notes"]),
            response_mode=str(support_package["emotion_analysis"]["response_mode"]),
            language=str(support_package["emotion_analysis"]["language"]),
            source=str(support_package["emotion_analysis"]["source"]),
            provider_name=str(support_package["emotion_analysis"]["provider_name"]),
        ),
        topic_tags=list(support_package["topic_tags"]),
        risk_level=str(support_package["risk_level"]),
        risk_flags=list(support_package["risk_flags"]),
        response_plan=ResponsePlanResponse(**support_package["response_plan"]),
        empathetic_response=str(support_package["empathetic_response"]),
        follow_up_question=(
            str(support_package["follow_up_question"]) if support_package["follow_up_question"] is not None else None
        ),
        gentle_suggestion=(
            str(support_package["gentle_suggestion"]) if support_package["gentle_suggestion"] is not None else None
        ),
        quote=ResponseQuoteResponse(**quote.model_dump()) if quote is not None else None,
        ai_response=str(support_package["ai_response"]),
        ai=AIContractResponse.model_validate(
            build_ai_contract(
                emotion_analysis=support_package["emotion_analysis"],
                risk_level=str(support_package["risk_level"]),
                risk_flags=list(support_package["risk_flags"]),
                topic_tags=list(support_package["topic_tags"]),
                response_plan=support_package["response_plan"],
                empathetic_response=str(support_package["empathetic_response"]),
                follow_up_question=(
                    str(support_package["follow_up_question"]) if support_package["follow_up_question"] is not None else None
                ),
                gentle_suggestion=(
                    str(support_package["gentle_suggestion"]) if support_package["gentle_suggestion"] is not None else None
                ),
                quote=quote.model_dump() if quote is not None else None,
                ai_response=str(support_package["ai_response"]),
                normalized_state=support_package.get("normalized_state"),
                support_strategy=support_package.get("support_strategy"),
                memory_summary=support_package.get("memory_summary"),
                insight_features=support_package.get("insight_features"),
            )
        ),
    )
