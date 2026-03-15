from fastapi import APIRouter, Query

router = APIRouter(prefix="/v1/resources", tags=["resources"])

CRISIS_RESOURCES = {
    "VN": {
        "country": "VN",
        "emergency_contacts": ["113", "115"],
        "crisis_hotlines": ["Please contact local emergency support or a trusted person nearby if you feel unsafe."],
        "notes": [
            "This list is a lightweight informational fallback and may not be complete.",
            "If there is immediate danger, prioritize local emergency services.",
        ],
    },
    "US": {
        "country": "US",
        "emergency_contacts": ["911"],
        "crisis_hotlines": ["988 Suicide & Crisis Lifeline"],
        "notes": [
            "Call or text 988 in the United States for crisis support.",
            "This endpoint is informational and not medical advice.",
        ],
    },
    "DEFAULT": {
        "country": "DEFAULT",
        "emergency_contacts": [],
        "crisis_hotlines": ["Reach out to local emergency services or a trusted person near you."],
        "notes": [
            "This list is not complete.",
            "If you may be in immediate danger, use local emergency services where you are.",
        ],
    },
}


@router.get("/crisis")
def get_crisis_resources(country: str = Query("VN")) -> dict[str, object]:
    normalized = country.upper()
    return CRISIS_RESOURCES.get(normalized, CRISIS_RESOURCES["DEFAULT"])
