import re

from app.services.companion_core.schemas import RenderContext


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


_NAMED_TARGET_RE = re.compile(
    r"^\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:seems|looks|is)\s+(?:sad|angry|upset|mad|hurt|ill|sick|stressed|anxious|overwhelmed|down)\b"
)
_OTHER_PERSON_STATE_RE = re.compile(
    r"\b(?:seems|looks|appears|is)\s+(?:really\s+|so\s+|very\s+)?(sad|angry|upset|mad|hurt|ill|sick|stressed|anxious|overwhelmed|down)\b"
)


def _extract_named_target(text: str) -> str | None:
    match = _NAMED_TARGET_RE.match(text.strip())
    if not match:
        return None
    candidate = match.group(1).strip()
    if candidate.casefold() in {"i", "my"}:
        return None
    return candidate


def _extract_other_person_emotion_word(text: str) -> str | None:
    match = _OTHER_PERSON_STATE_RE.search(text.casefold())
    if not match:
        return None
    return match.group(1)


def detect_render_context(text: str, topic_tags: list[str], context_tag: str | None = None) -> RenderContext:
    normalized = text.casefold().strip()
    tokens = normalized.split()
    evidence_spans: list[str] = []

    relationship_terms = {
        "crush": "crush",
        "girlfriend": "girlfriend",
        "boyfriend": "boyfriend",
        "partner": "partner",
        "wife": "wife",
        "husband": "husband",
        "friend": "friend",
        "mom": "mom",
        "mother": "mother",
        "dad": "dad",
        "father": "father",
        "sister": "sister",
        "brother": "brother",
        "teammate": "teammate",
        "coworker": "coworker",
        "colleague": "colleague",
        "manager": "manager",
        "boss": "boss",
        "classmate": "classmate",
        "mentor": "mentor",
        "roommate": "roommate",
    }
    health_terms = ("sick", "ill", "fever", "hospital", "hurt", "not well", "unwell", "doctor")
    deadline_terms = ("deadline", "deadlines", "due", "assignment", "exam", "project", "packed tight", "piling up")
    completion_terms = ("finally", "finished", "done", "submitted", "got it done", "completed")
    loneliness_terms = ("left behind", "left out", "lonely", "lạc lõng", "alone", "hard to reach", "disconnected")
    low_energy_terms = ("tired", "drained", "low on battery", "empty", "flat", "exhausted", "numb", "slower")
    appreciation_terms = (
        "told me i'd be good",
        "told me i would be good",
        "told me i'd actually be good",
        "told me i would actually be good",
        "said i'd be good",
        "said i would be good",
        "good at helping",
        "good at this",
        "appreciated",
        "proud of me",
        "recognized",
        "recognition",
        "thankful",
        "grateful",
        "kindness",
    )
    positive_terms = ("likes me", "likes me back", "said yes", "asked me out", "good news", "excited", "happy")
    rejection_terms = ("don't like me", "doesn't like me", "do not like me", "does not like me", "not into me", "rejected me", "ghosted me")
    responsibility_terms = (
        "let them down",
        "let her down",
        "let him down",
        "let my teammate down",
        "let my friend down",
        "let my partner down",
        "disappointed",
        "dropped the ball",
        "messed up",
        "failed them",
        "missed it",
        "forgot",
        "owe them",
        "late replying",
        "didn't finish on time",
        "did not finish on time",
        "missed the deadline",
        "missed deadline",
    )
    mixed_terms = ("at the same time", "weirdly", "not sure", "mixed", "both", "part of me")
    greeting_terms = ("hello", "hi", "hey", "good morning", "good evening", "good afternoon")
    other_person_state_terms = (
        "angry",
        "upset",
        "sad",
        "crying",
        "mad",
        "sick",
        "ill",
        "hurt",
        "stressed",
        "stress",
        "anxious",
        "overwhelmed",
        "down",
    )
    distress_terms = (
        "i feel",
        "i've been",
        "i have been",
        "can't stop",
        "cannot stop",
        "worried",
        "anxious",
        "overwhelmed",
        "stressed",
        "pressure",
    )

    relationship_target = None
    relationship_role = None
    for term, label in relationship_terms.items():
        if term in normalized:
            relationship_target = label
            relationship_role = label
            evidence_spans.append(term)
            break
    if relationship_target is None:
        named_target = _extract_named_target(text)
        if named_target is not None:
            relationship_target = named_target
            relationship_role = "named_person"
            evidence_spans.append(named_target)

    def _match_terms(terms: tuple[str, ...]) -> list[str]:
        return [term for term in terms if term in normalized]

    health_matches = _match_terms(health_terms)
    deadline_matches = _match_terms(deadline_terms)
    completion_matches = _match_terms(completion_terms)
    loneliness_matches = _match_terms(loneliness_terms)
    low_energy_matches = _match_terms(low_energy_terms)
    appreciation_matches = _match_terms(appreciation_terms)
    positive_matches = _match_terms(positive_terms)
    rejection_matches = _match_terms(rejection_terms)
    responsibility_matches = _match_terms(responsibility_terms)
    if "let " in normalized and " down" in normalized:
        responsibility_matches.append("let ... down")
    mixed_matches = _match_terms(mixed_terms)
    distress_matches = _match_terms(distress_terms)
    other_person_state_matches = _match_terms(other_person_state_terms)
    greeting_matches = [term for term in greeting_terms if normalized == term]
    explicit_other_state = any(phrase in normalized for phrase in ("seems ", "looks ", "appears "))
    other_person_emotion_word = _extract_other_person_emotion_word(text)
    self_responsibility_markers = any(
        phrase in normalized
        for phrase in (
            "because i ",
            "because i'",
            "since i ",
            "after i ",
            "i let",
            "i didn't finish",
            "i did not finish",
            "missed the deadline",
            "missed deadline",
        )
    )

    evidence_spans.extend(
        health_matches
        + deadline_matches
        + completion_matches
        + loneliness_matches
        + low_energy_matches
        + appreciation_matches
        + positive_matches
        + rejection_matches
        + responsibility_matches
        + mixed_matches
        + distress_matches
        + other_person_state_matches
        + greeting_matches
    )

    relationship_concern = relationship_target is not None
    health_related_update = bool(health_matches)
    appreciation_or_recognition = bool(appreciation_matches) or ("told me" in normalized and "good at" in normalized)
    positive_personal_update = bool(positive_matches)
    low_energy_update = bool(low_energy_matches)
    responsibility_tension = bool(responsibility_matches)
    distress_checkin = bool(distress_matches)
    reflective_checkin = len(tokens) > 8 or "i keep" in normalized or "part of me" in normalized or bool(mixed_matches)
    short_personal_update = len(tokens) <= 6
    short_event_flag = short_personal_update and not distress_checkin
    other_person_state_mentioned = relationship_concern and (bool(other_person_state_matches) or explicit_other_state)
    greeting_only = bool(greeting_matches) and len(tokens) <= 3 and not relationship_concern and not distress_checkin

    deadline_relief = bool(deadline_matches) and bool(completion_matches)

    if greeting_only:
        utterance_type = "short_personal_update"
        event_type = "greeting_or_opening"
        user_stance = "seeking_contact"
    elif relationship_concern and health_related_update:
        utterance_type = "relationship_concern"
        event_type = "loved_one_unwell"
        user_stance = "worried_about_other"
    elif relationship_target in {"crush", "girlfriend", "boyfriend", "partner"} and rejection_matches:
        utterance_type = "relationship_concern"
        event_type = "uncertain_romantic_rejection"
        user_stance = "hurt_by_rejection"
    elif appreciation_or_recognition:
        utterance_type = "appreciation_or_recognition"
        event_type = "recognition_or_praise"
        user_stance = "encouraged_by_other"
    elif responsibility_tension or (other_person_state_mentioned and self_responsibility_markers):
        utterance_type = "responsibility_tension"
        event_type = "responsibility_tension"
        user_stance = "guilty_toward_other"
    elif other_person_state_mentioned:
        utterance_type = "relationship_concern"
        event_type = "other_person_distress"
        user_stance = "worried_about_other"
    elif low_energy_update and (mixed_matches or ("relieved" in normalized or "relief" in normalized)):
        utterance_type = "reflective_checkin"
        event_type = "uncertain_mixed_state"
        user_stance = "processing_self"
    elif low_energy_update:
        utterance_type = "low_energy_update"
        event_type = "exhaustion_or_flatness"
        user_stance = "processing_self"
    elif deadline_relief:
        utterance_type = "short_personal_update" if short_personal_update else "reflective_checkin"
        event_type = "relief_or_gratitude"
        user_stance = "processing_self"
    elif deadline_matches:
        utterance_type = "distress_checkin" if distress_checkin else "reflective_checkin"
        event_type = "deadline_pressure"
        user_stance = "processing_self"
    elif loneliness_matches:
        utterance_type = "reflective_checkin"
        event_type = "loneliness_or_disconnection"
        user_stance = "processing_self"
    elif positive_personal_update:
        utterance_type = "short_personal_update" if short_personal_update else "reflective_checkin"
        event_type = "relief_or_gratitude"
        user_stance = "processing_self"
    elif "grateful" in normalized or "relieved" in normalized or "kindness" in normalized:
        utterance_type = "reflective_checkin"
        event_type = "relief_or_gratitude"
        user_stance = "processing_self"
    elif distress_checkin:
        utterance_type = "distress_checkin"
        event_type = (
            "uncertain_mixed_state"
            if mixed_matches
            else "deadline_pressure"
            if topic_tags and topic_tags[0] == "work/school"
            else "uncertain_mixed_state"
        )
        user_stance = "processing_self"
    elif short_personal_update:
        utterance_type = "short_personal_update"
        event_type = "uncertain_mixed_state"
        user_stance = "processing_self"
    else:
        utterance_type = "reflective_checkin"
        event_type = "uncertain_mixed_state"
        user_stance = "processing_self"

    social_context = "solo"
    if relationship_target in {"girlfriend", "boyfriend", "partner", "wife", "husband"}:
        social_context = "romantic_relationship"
    elif relationship_target in {"mom", "mother", "dad", "father", "sister", "brother"}:
        social_context = "family"
    elif relationship_target == "friend":
        social_context = "friendship"
    elif relationship_target in {"teammate", "coworker", "colleague", "manager", "boss", "classmate", "mentor"}:
        social_context = "work_or_school"
    elif deadline_matches:
        social_context = "work_or_school"
    elif context_tag and context_tag.strip():
        social_context = context_tag.strip().replace(" ", "_")

    emotion_owner_hint = "user"
    if event_type in {"other_person_distress", "loved_one_unwell"}:
        emotion_owner_hint = "other_person"
    elif relationship_concern and other_person_state_mentioned:
        emotion_owner_hint = "mixed"

    return RenderContext(
        utterance_type=utterance_type,
        event_type=event_type,
        relationship_target=relationship_target,
        relationship_role=relationship_role,
        relationship_concern=relationship_concern,
        health_related_update=health_related_update,
        short_personal_update=short_personal_update,
        short_event_flag=short_event_flag,
        low_energy_update=low_energy_update,
        appreciation_or_recognition=appreciation_or_recognition,
        positive_personal_update=positive_personal_update,
        reflective_checkin=reflective_checkin,
        responsibility_tension=responsibility_tension,
        distress_checkin=distress_checkin,
        user_stance=user_stance,
        social_context=social_context,
        concern_target=relationship_target,
        other_person_state_mentioned=other_person_state_mentioned,
        other_person_emotion_word=other_person_emotion_word,
        emotion_owner_hint=emotion_owner_hint,
        greeting_only=greeting_only,
        suggestion_allowed=True,
        evidence_spans=_dedupe(evidence_spans),
    )
