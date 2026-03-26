from __future__ import annotations

import logging
import re

from app.services.provider_errors import ProviderExecutionError
from app.services.response_policy_service import build_follow_up_question, build_suggestion_text

logger = logging.getLogger(__name__)

CLINICAL_BLOCKLIST = (
    "diagnos",
    "disorder",
    "clinical",
    "medication",
    "bipolar",
    "ptsd",
    "depression",
    "anxiety disorder",
)
UNSUPPORTED_PHRASES = (
    "missed deadline",
    "missed the deadline",
    "conflict",
    "argument",
    "failure",
    "they said",
)
UNSUPPORTED_PATTERNS = (
    re.compile(r"\bbecause\s+[^.?!]{0,80}\bhappened\b", re.IGNORECASE),
)
REDUNDANT_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "i",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "right",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "your",
}


def _contains_clinical_claim(text: str) -> bool:
    lowered = text.casefold()
    return any(term in lowered for term in CLINICAL_BLOCKLIST)


def _trim_sentences(text: str, max_sentences: int) -> str:
    chunks = [chunk.strip() for chunk in text.replace("?", ".").replace("!", ".").split(".") if chunk.strip()]
    if not chunks:
        return ""
    return ". ".join(chunks[:max_sentences]).strip() + ("." if chunks[:max_sentences] else "")


def _contains_unsupported_specifics(text: str, transcript: str) -> bool:
    lowered_text = text.casefold()
    lowered_transcript = transcript.casefold()
    for phrase in UNSUPPORTED_PHRASES:
        if phrase in lowered_text and phrase not in lowered_transcript:
            return True
    return any(pattern.search(text) and not pattern.search(transcript) for pattern in UNSUPPORTED_PATTERNS)


def _normalize_overlap_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z']+", text.casefold())
        if len(token) > 2 and token not in REDUNDANT_STOPWORDS
    }


def _strip_repeated_lead(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(
        r"^(it sounds like|it feels like|it can be hard when|it makes sense if)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def _soften_template_phrasing(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(
        r"^You're really noticing that (.+) seems ([a-z]+) right now\.$",
        r"Seeing \1 seem \2 can really stay with you.",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^What feels most present for you as you sit with this\?$",
        "What feels heaviest here for you?",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned


def _is_redundant(candidate: str | None, *others: str | None) -> bool:
    if not candidate:
        return False
    normalized_candidate = candidate.casefold().strip(" .?!")
    candidate_tokens = _normalize_overlap_tokens(candidate)
    if not candidate_tokens:
        return False

    for other in others:
        if not other:
            continue
        normalized_other = other.casefold().strip(" .?!")
        if not normalized_other:
            continue
        if normalized_candidate in normalized_other or normalized_other in normalized_candidate:
            return True
        other_tokens = _normalize_overlap_tokens(other)
        if not other_tokens:
            continue
        overlap = len(candidate_tokens & other_tokens) / max(len(candidate_tokens), 1)
        if overlap >= 0.64:
            return True
    return False


def postcheck_rendered_response(
    *,
    rendered: dict[str, object],
    response_plan: dict[str, object],
    fallback_empathetic_text: str,
    quote_text: str | None,
    transcript: str,
    language: str = "en",
) -> dict[str, object]:
    response_mode = str(response_plan.get("response_mode", ""))
    response_variant = str(response_plan.get("response_variant", "empathy_only"))
    suggestion_family = response_plan.get("suggestion_family")
    unsupported_specifics_detected = False
    empathetic_text = str(rendered.get("empathetic_text") or "").strip()
    if not empathetic_text:
        raise ProviderExecutionError("Gemini response rendering returned empty empathetic_text")
    if _contains_clinical_claim(empathetic_text) or _contains_unsupported_specifics(empathetic_text, transcript):
        unsupported_specifics_detected = True
        empathetic_text = fallback_empathetic_text

    follow_up_question = rendered.get("follow_up_question")
    if not response_plan.get("follow_up_question_allowed"):
        follow_up_question = None
    elif isinstance(follow_up_question, str):
        follow_up_question = follow_up_question.strip() or None
    else:
        follow_up_question = None

    suggestion_text = rendered.get("suggestion_text")
    if not response_plan.get("suggestion_allowed"):
        suggestion_text = None
    elif isinstance(suggestion_text, str):
        suggestion_text = suggestion_text.strip() or None
    else:
        suggestion_text = None

    if response_plan.get("avoid_advice") and suggestion_text is not None:
        suggestion_text = None
    if suggestion_text is not None and _contains_unsupported_specifics(suggestion_text, transcript):
        unsupported_specifics_detected = True
        suggestion_text = None
    if follow_up_question is not None and _contains_unsupported_specifics(follow_up_question, transcript):
        unsupported_specifics_detected = True
        follow_up_question = None
    if unsupported_specifics_detected:
        logger.warning(
            "response_postcheck.repaired_unsupported_specifics response_variant=%s response_mode=%s language=%s",
            response_variant,
            response_mode,
            language,
        )

    if unsupported_specifics_detected and not empathetic_text:
        empathetic_text = fallback_empathetic_text

    fallback_suggestion = build_suggestion_text(
        suggestion_family=str(suggestion_family) if suggestion_family is not None else None,
        language=language,
        render_context=dict(response_plan.get("render_context", {})),
        normalized_state=dict(response_plan.get("normalized_state", {})),
        support_strategy=dict(response_plan.get("support_strategy", {})),
    )
    fallback_follow_up = build_follow_up_question(
        response_mode=response_mode,
        language=language,
        render_context=dict(response_plan.get("render_context", {})),
        normalized_state=dict(response_plan.get("normalized_state", {})),
        support_strategy=dict(response_plan.get("support_strategy", {})),
    )

    # Enforce one coherent output variant.
    if response_variant == "empathy_only":
        suggestion_text = None
        follow_up_question = None
        effective_quote_allowed = False
    elif response_variant == "empathy_plus_suggestion":
        follow_up_question = None
        effective_quote_allowed = False
        if suggestion_text is None and bool(response_plan.get("suggestion_allowed")):
            suggestion_text = fallback_suggestion
    elif response_variant == "empathy_plus_followup":
        suggestion_text = None
        effective_quote_allowed = False
        if follow_up_question is None and bool(response_plan.get("follow_up_question_allowed")):
            follow_up_question = fallback_follow_up
    elif response_variant == "empathy_plus_quote":
        suggestion_text = None
        follow_up_question = None
        effective_quote_allowed = True
    else:
        # Fail closed if planner data is missing or invalid.
        suggestion_text = None
        follow_up_question = None
        effective_quote_allowed = False

    if unsupported_specifics_detected and response_variant == "empathy_plus_followup" and follow_up_question is None:
        follow_up_question = fallback_follow_up
    if unsupported_specifics_detected and response_variant == "empathy_plus_suggestion":
        suggestion_text = fallback_suggestion
        follow_up_question = None

    if follow_up_question is not None and not follow_up_question.endswith("?"):
        follow_up_question = follow_up_question.rstrip(". ") + "?"

    empathetic_text = _soften_template_phrasing(empathetic_text)
    if follow_up_question is not None:
        follow_up_question = _soften_template_phrasing(follow_up_question)

    cleaned_empathy = _strip_repeated_lead(empathetic_text)
    if cleaned_empathy:
        empathetic_text = (
            cleaned_empathy[0].upper() + cleaned_empathy[1:]
            if len(cleaned_empathy) > 1
            else cleaned_empathy.upper()
        )

    if suggestion_text is not None and _is_redundant(suggestion_text, empathetic_text, follow_up_question):
        suggestion_text = None
    if follow_up_question is not None and _is_redundant(follow_up_question, empathetic_text, suggestion_text):
        follow_up_question = None
        if response_variant == "empathy_plus_followup" and bool(response_plan.get("follow_up_question_allowed")):
            follow_up_question = fallback_follow_up
            if follow_up_question is not None and not follow_up_question.endswith("?"):
                follow_up_question = follow_up_question.rstrip(". ") + "?"
            if follow_up_question is not None and _is_redundant(follow_up_question, empathetic_text):
                follow_up_question = None

    effective_quote_text = quote_text if response_plan.get("quote_allowed") and effective_quote_allowed else None
    max_sentences = int(response_plan.get("max_sentences", 3))
    empathetic_text = _trim_sentences(empathetic_text, max_sentences)
    if suggestion_text is not None:
        suggestion_text = _trim_sentences(suggestion_text, 1)
    if follow_up_question is not None:
        follow_up_question = follow_up_question[:180]

    composed_parts = [empathetic_text]
    if suggestion_text:
        composed_parts.append(suggestion_text)
    if follow_up_question:
        composed_parts.append(follow_up_question)
    if effective_quote_text:
        composed_parts.append(effective_quote_text)
    composed_text = " ".join(part for part in composed_parts if part)
    logger.info(
        "response_postcheck.complete response_variant=%s response_mode=%s has_suggestion=%s has_follow_up=%s has_quote=%s",
        response_variant,
        response_mode,
        bool(suggestion_text),
        bool(follow_up_question),
        bool(effective_quote_text),
    )

    return {
        "empathetic_text": empathetic_text,
        "follow_up_question": follow_up_question,
        "suggestion_text": suggestion_text,
        "quote_text": effective_quote_text,
        "composed_text": composed_text,
    }
