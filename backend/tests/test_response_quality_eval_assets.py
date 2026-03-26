import json
from pathlib import Path


DATASET_PATH = Path(__file__).resolve().parents[1] / "evals" / "response_quality_cases.json"


def test_response_quality_eval_dataset_has_expected_shape() -> None:
    payload = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    assert isinstance(payload, list)
    assert 30 <= len(payload) <= 50

    categories = {str(item["category"]) for item in payload}
    expected_categories = {
        "greeting_opening",
        "neutral_checkin",
        "self_sadness",
        "self_stress_overload",
        "guilt_regret",
        "positive_relief_gratitude",
        "other_person_concern",
        "ambiguous_emotion_ownership",
        "work_pressure_deadline",
        "low_energy_emptiness",
        "frustration_not_heard",
        "mixed_recovery_improvement",
    }

    assert expected_categories.issubset(categories)

    for item in payload:
        assert item["id"]
        assert item["input_text"]
        assert item["should_do"]
        assert item["should_avoid"]
        assert item["review_focus"]
