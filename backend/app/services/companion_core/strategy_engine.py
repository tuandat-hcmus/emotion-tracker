from app.services.companion_core.schemas import MemorySummary, NormalizedEmotionalState, SupportStrategy


def select_support_strategy(
    state: NormalizedEmotionalState,
    memory_summary: MemorySummary | None = None,
) -> SupportStrategy:
    rationale: list[str] = []
    recurring_trigger = memory_summary and state.event_type in set(memory_summary.recurring_triggers)
    recurring_context = memory_summary and state.social_context in set(memory_summary.recurring_social_contexts)
    repeated_loneliness = memory_summary and "loneliness_or_disconnection" in set(memory_summary.dominant_negative_patterns)
    repeated_work_strain = memory_summary and (
        "deadline_pressure" in set(memory_summary.dominant_negative_patterns)
        or "work_or_school" in set(memory_summary.recurring_social_contexts)
    )

    if state.risk_level in {"high", "medium"}:
        rationale.append("risk boundary overrides normal companion behavior")
        return SupportStrategy(
            support_focus="user",
            strategy_type="safe_support",
            suggestion_budget="none",
            personalization_tone="gentle",
            response_goal="feel_heard",
            rationale=rationale,
        )

    if state.user_stance == "encouraged_by_other" or state.event_type == "recognition_or_praise":
        rationale.append("recognition from another person should be reinforced rather than flattened")
        return SupportStrategy(
            support_focus="user",
            strategy_type="celebratory_warm",
            suggestion_budget="minimal",
            personalization_tone="soft_celebratory",
            response_goal="reinforce_positive_moment",
            rationale=rationale,
        )

    if state.user_stance == "worried_about_other" or state.event_type in {"loved_one_unwell", "other_person_distress"}:
        rationale.append("the user's state is organized around concern for another person")
        if recurring_context:
            rationale.append("relationship-centered patterns have appeared recently")
        return SupportStrategy(
            support_focus="relationship",
            strategy_type="supportive_reflective",
            suggestion_budget="minimal",
            personalization_tone="gentle",
            response_goal="reduce_aloneness",
            rationale=rationale,
        )

    if state.user_stance == "guilty_toward_other" or state.event_type == "responsibility_tension":
        rationale.append("responsibility and interpersonal tension require validation before grounding")
        if recurring_trigger or recurring_context:
            rationale.append("similar responsibility strain has appeared recently")
        return SupportStrategy(
            support_focus="relationship",
            strategy_type="validating_gentle",
            suggestion_budget="none" if state.stress >= 0.7 else "minimal",
            personalization_tone="gentle",
            response_goal="repair_without_spiral",
            rationale=rationale,
        )

    if state.user_stance == "hurt_by_rejection" or state.event_type == "uncertain_romantic_rejection":
        rationale.append("romantic ambiguity or rejection should be handled as hurt, not generic mixedness")
        return SupportStrategy(
            support_focus="user",
            strategy_type="low_energy_comfort" if state.energy <= 0.45 else "supportive_reflective",
            suggestion_budget="none" if state.stress >= 0.55 else "minimal",
            personalization_tone="gentle",
            response_goal="reduce_aloneness",
            rationale=rationale,
        )

    if state.event_type == "deadline_pressure" or state.response_mode == "stress_supportive":
        rationale.append("deadline and workload pressure are central to the user's distress")
        if repeated_work_strain or recurring_trigger:
            rationale.append("recent memory suggests this pressure pattern has been repeating")
        if state.stress >= 0.72:
            rationale.append("the current load is high enough that grounding should stay concrete and brief")
        return SupportStrategy(
            support_focus="user",
            strategy_type="stress_supportive",
            suggestion_budget="none" if state.stress >= 0.72 else "minimal",
            personalization_tone="steady_grounding",
            response_goal="reduce_pressure_spiral",
            rationale=rationale,
        )

    if state.valence >= 0.35 and state.stress <= 0.25:
        rationale.append("positive valence with low stress supports warm reinforcement")
        if recurring_trigger:
            rationale.append("this positive pattern has shown up more than once recently")
        return SupportStrategy(
            support_focus="user",
            strategy_type="celebratory_warm",
            suggestion_budget="minimal",
            personalization_tone="soft_celebratory",
            response_goal="reinforce_positive_moment",
            rationale=rationale,
        )

    if state.event_type in {"loved_one_unwell"} or state.social_context in {"romantic_relationship", "family"} and state.concern_target:
        rationale.append("another person is central to the emotional event")
        if recurring_context:
            rationale.append("relationship-centered patterns have appeared recently")
        return SupportStrategy(
            support_focus="relationship",
            strategy_type="supportive_reflective",
            suggestion_budget="minimal",
            personalization_tone="gentle",
            response_goal="reduce_aloneness",
            rationale=rationale,
        )

    if state.event_type == "conflict_or_disappointment":
        rationale.append("interpersonal tension or guilt-like strain is present")
        if recurring_trigger or recurring_context:
            rationale.append("this tension pattern has repeated recently")
        return SupportStrategy(
            support_focus="mixed",
            strategy_type="validating_gentle",
            suggestion_budget="none" if recurring_context else "minimal",
            personalization_tone="gentle",
            response_goal="feel_heard",
            rationale=rationale,
        )

    if state.valence <= -0.12 and state.energy <= 0.3:
        rationale.append("negative low-energy state calls for soft, low-pressure support")
        if repeated_loneliness:
            rationale.append("recent memory shows a recurring disconnection pattern")
        return SupportStrategy(
            support_focus="user",
            strategy_type="low_energy_comfort",
            suggestion_budget="none" if repeated_loneliness else "minimal",
            personalization_tone="low_stimulation",
            response_goal="reduce_aloneness",
            rationale=rationale,
        )

    if state.stress >= 0.6 or (state.valence <= -0.2 and state.energy >= 0.45):
        rationale.append("high emotional load requires grounding rather than advice")
        if repeated_work_strain or recurring_trigger:
            rationale.append("recent memory suggests repeated pressure, so validation should stay simple")
        return SupportStrategy(
            support_focus="user",
            strategy_type="grounding_soft",
            suggestion_budget="none" if repeated_work_strain else "minimal",
            personalization_tone="gentle",
            response_goal="gentle_orientation",
            rationale=rationale,
        )

    rationale.append("default everyday companion mode")
    if recurring_trigger:
        rationale.append("a recurring pattern is present in recent memory")
    return SupportStrategy(
        support_focus="user",
        strategy_type="supportive_reflective",
        suggestion_budget="minimal" if state.confidence >= 0.45 and not recurring_trigger else "none",
        personalization_tone="gentle",
        response_goal="feel_heard",
        rationale=rationale,
    )
