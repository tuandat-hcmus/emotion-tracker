from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.services.companion_core import build_companion_pipeline
from app.services.emotion_service import analyze_emotion
from app.services.response_service import get_response_provider_name, render_supportive_response
from app.services.safety_service import detect_safety_risk
from app.services.topic_service import tag_topics

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "evals" / "response_quality_cases.json"
DEFAULT_RESULTS_DIR = ROOT / "evals" / "results"
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "for",
    "from",
    "here",
    "i",
    "if",
    "in",
    "is",
    "it",
    "like",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "your",
}
STOCK_PHRASE_PATTERNS = {
    "stock_it_sounds_like": re.compile(r"\bit sounds like\b", re.IGNORECASE),
    "stock_youre_really_noticing": re.compile(r"\byou(?:'|’)re really noticing\b", re.IGNORECASE),
    "stock_what_feels_most_present": re.compile(r"\bwhat feels most present\b", re.IGNORECASE),
    "stock_as_you_sit_with_this": re.compile(r"\bas you sit with this\b", re.IGNORECASE),
}
OWNER_DRIFT_PATTERNS = (
    re.compile(r"\byou seem (sad|upset|stressed|overwhelmed)\b", re.IGNORECASE),
    re.compile(r"\byour (sadness|stress|upset|overwhelm)\b", re.IGNORECASE),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a lightweight backend companion response quality evaluation.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Path to the evaluation dataset JSON file.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR, help="Directory to write result artifacts into.")
    parser.add_argument("--run-name", type=str, default="", help="Optional run name. Defaults to a UTC timestamp.")
    parser.add_argument("--provider", type=str, default="", help="Optional response provider override, such as 'mock' or 'gemini'.")
    parser.add_argument("--limit", type=int, default=0, help="Optional number of dataset rows to run.")
    parser.add_argument("--category", type=str, default="", help="Optional category filter.")
    parser.add_argument("--case-id", type=str, default="", help="Optional single case id filter.")
    parser.add_argument("--baseline", type=Path, default=None, help="Optional prior results.json file to compare against.")
    return parser.parse_args()


def load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Dataset must be a JSON array.")
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Dataset row {index} must be an object.")
        for required_key in ("id", "category", "input_text", "should_do", "should_avoid", "review_focus"):
            if required_key not in item:
                raise ValueError(f"Dataset row {index} is missing required key '{required_key}'.")
    return payload


def select_cases(cases: list[dict[str, Any]], *, limit: int, category: str, case_id: str) -> list[dict[str, Any]]:
    selected = cases
    if category:
        selected = [case for case in selected if str(case.get("category")) == category]
    if case_id:
        selected = [case for case in selected if str(case.get("id")) == case_id]
    if limit > 0:
        selected = selected[:limit]
    return selected


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.casefold())


def _content_words(text: str) -> set[str]:
    return {word for word in _words(text) if word not in STOPWORDS}


def _first_tokens(text: str, *, count: int) -> str:
    words = _words(text)
    return " ".join(words[:count]) if words else ""


def _jaccard(left: str | None, right: str | None) -> float:
    left_words = _content_words(left or "")
    right_words = _content_words(right or "")
    if not left_words or not right_words:
        return 0.0
    union = left_words | right_words
    if not union:
        return 0.0
    return len(left_words & right_words) / len(union)


def _sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


def _question_count(text: str) -> int:
    return text.count("?")


def _stock_phrase_hits(text: str) -> list[str]:
    return [label for label, pattern in STOCK_PHRASE_PATTERNS.items() if pattern.search(text)]


def _other_person_owner_drift(text: str) -> bool:
    return any(pattern.search(text) for pattern in OWNER_DRIFT_PATTERNS)


def _issue_list(case: dict[str, Any], *, ai_response: str, empathetic_text: str, question: str | None, suggestion: str | None) -> list[str]:
    issues: list[str] = []
    max_words = int(case.get("max_words") or 0)
    word_count = len(_words(ai_response))
    if max_words and word_count > max_words:
        issues.append(f"too_long:{word_count}>{max_words}")
    if case.get("expect_question") is True and not question:
        issues.append("missing_expected_question")
    if case.get("expect_question") is False and question:
        issues.append("unexpected_question")
    if _question_count(ai_response) > 1:
        issues.append("multiple_questions")
    if _sentence_count(ai_response) > 3:
        issues.append("too_many_sentences")
    if _jaccard(empathetic_text, question) >= 0.45:
        issues.append("empathy_question_overlap")
    if _jaccard(empathetic_text, suggestion) >= 0.45:
        issues.append("empathy_suggestion_overlap")
    if question and suggestion and _jaccard(question, suggestion) >= 0.4:
        issues.append("question_suggestion_overlap")
    hits = _stock_phrase_hits(ai_response)
    issues.extend(hits)
    if case.get("self_vs_other_expected") == "other_person_concern" and _other_person_owner_drift(ai_response):
        issues.append("self_vs_other_owner_drift")
    return issues


def evaluate_case(case: dict[str, Any], *, provider_override: str | None) -> dict[str, Any]:
    transcript = str(case["input_text"])
    safety_result = detect_safety_risk(transcript)
    risk_level = str(safety_result["risk_level"])
    topic_tags = tag_topics(transcript)
    emotion_analysis = analyze_emotion(transcript, risk_level=risk_level)
    pipeline = build_companion_pipeline(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
    )
    response_payload = render_supportive_response(
        transcript=transcript,
        emotion_analysis=pipeline.emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        response_plan=pipeline.response_plan,
        memory_summary=pipeline.memory_summary.model_dump(),
        user_id="response-quality-eval",
        quote_opt_in=False,
        provider_override=provider_override or None,
    )
    ai_response = str(response_payload["ai_response"])
    empathetic_text = str(response_payload["empathetic_response"])
    question = response_payload.get("follow_up_question")
    suggestion = response_payload.get("gentle_suggestion")
    heuristics = {
        "word_count": len(_words(ai_response)),
        "sentence_count": _sentence_count(ai_response),
        "question_count": _question_count(ai_response),
        "opening_key": _first_tokens(ai_response, count=3),
        "question_key": _first_tokens(str(question or ""), count=6),
        "stock_phrase_hits": _stock_phrase_hits(ai_response),
        "empathy_question_overlap": round(_jaccard(empathetic_text, str(question or "")), 3),
        "empathy_suggestion_overlap": round(_jaccard(empathetic_text, str(suggestion or "")), 3),
        "question_suggestion_overlap": round(_jaccard(str(question or ""), str(suggestion or "")), 3),
        "self_vs_other_owner_drift": (
            _other_person_owner_drift(ai_response)
            if case.get("self_vs_other_expected") == "other_person_concern"
            else None
        ),
    }
    return {
        "id": case["id"],
        "category": case["category"],
        "input_text": transcript,
        "should_do": case["should_do"],
        "should_avoid": case["should_avoid"],
        "review_focus": case["review_focus"],
        "expect_question": case.get("expect_question"),
        "max_words": case.get("max_words"),
        "risk_level": risk_level,
        "topic_tags": topic_tags,
        "emotion_analysis": {
            "primary_label": pipeline.emotion_analysis.get("primary_label"),
            "primary_emotion": pipeline.emotion_analysis.get("primary_emotion"),
            "response_mode": pipeline.emotion_analysis.get("response_mode"),
            "provider_name": pipeline.emotion_analysis.get("provider_name"),
        },
        "render_context": pipeline.render_context.model_dump(),
        "normalized_state": pipeline.normalized_state.model_dump(),
        "support_strategy": pipeline.support_strategy.model_dump(),
        "response_plan_summary": {
            "response_variant": pipeline.response_plan.get("response_variant"),
            "response_mode": pipeline.response_plan.get("response_mode"),
            "follow_up_question_allowed": pipeline.response_plan.get("follow_up_question_allowed"),
            "suggestion_allowed": pipeline.response_plan.get("suggestion_allowed"),
        },
        "response": {
            "provider_name": response_payload.get("provider_name"),
            "empathetic_response": empathetic_text,
            "follow_up_question": question,
            "gentle_suggestion": suggestion,
            "ai_response": ai_response,
        },
        "heuristics": heuristics,
        "issues": _issue_list(
            case,
            ai_response=ai_response,
            empathetic_text=empathetic_text,
            question=str(question or ""),
            suggestion=str(suggestion or ""),
        ),
    }


def _safe_run_case(case: dict[str, Any], *, provider_override: str | None) -> dict[str, Any]:
    try:
        return evaluate_case(case, provider_override=provider_override)
    except Exception as exc:  # pragma: no cover - used for practical eval reporting
        return {
            "id": case["id"],
            "category": case["category"],
            "input_text": case["input_text"],
            "should_do": case["should_do"],
            "should_avoid": case["should_avoid"],
            "review_focus": case["review_focus"],
            "response": {
                "provider_name": None,
                "empathetic_response": None,
                "follow_up_question": None,
                "gentle_suggestion": None,
                "ai_response": None,
            },
            "heuristics": {},
            "issues": [f"pipeline_error:{type(exc).__name__}"],
            "error": str(exc),
        }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(result["category"] for result in results)
    issue_counts = Counter(issue for result in results for issue in result.get("issues", []))
    opening_counts = Counter(
        result.get("heuristics", {}).get("opening_key")
        for result in results
        if result.get("heuristics", {}).get("opening_key")
    )
    question_counts = Counter(
        result.get("heuristics", {}).get("question_key")
        for result in results
        if result.get("heuristics", {}).get("question_key")
    )
    repeated_openings = {key: count for key, count in opening_counts.items() if count >= 3}
    repeated_questions = {key: count for key, count in question_counts.items() if count >= 3}
    total = len(results)
    successful = sum(1 for result in results if "error" not in result)
    avg_words = round(
        sum(result.get("heuristics", {}).get("word_count", 0) for result in results if "error" not in result) / successful,
        2,
    ) if successful else 0.0
    category_issue_breakdown: dict[str, dict[str, int]] = defaultdict(dict)
    for category in category_counts:
        category_issue_breakdown[category] = dict(
            Counter(
                issue
                for result in results
                if result["category"] == category
                for issue in result.get("issues", [])
            )
        )
    return {
        "total_cases": total,
        "successful_cases": successful,
        "failed_cases": total - successful,
        "average_word_count": avg_words,
        "category_counts": dict(category_counts),
        "issue_counts": dict(issue_counts),
        "repeated_openings": repeated_openings,
        "repeated_questions": repeated_questions,
        "category_issue_breakdown": category_issue_breakdown,
    }


def _load_baseline(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def compare_against_baseline(current_results: list[dict[str, Any]], baseline_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if baseline_payload is None:
        return None
    baseline_results = {
        str(item["id"]): item
        for item in baseline_payload.get("results", [])
        if isinstance(item, dict) and "id" in item
    }
    changed_cases: list[dict[str, Any]] = []
    for result in current_results:
        baseline = baseline_results.get(str(result["id"]))
        if not baseline:
            continue
        current_text = str(result.get("response", {}).get("ai_response") or "")
        baseline_text = str(baseline.get("response", {}).get("ai_response") or "")
        if current_text == baseline_text:
            continue
        changed_cases.append(
            {
                "id": result["id"],
                "category": result["category"],
                "before": baseline_text,
                "after": current_text,
                "word_count_delta": (
                    int(result.get("heuristics", {}).get("word_count", 0))
                    - int(baseline.get("heuristics", {}).get("word_count", 0))
                ),
                "issue_delta": (
                    len(result.get("issues", []))
                    - len(baseline.get("issues", []))
                ),
            }
        )
    return {
        "baseline_path": str(baseline_payload.get("metadata", {}).get("source_path", "")) or None,
        "changed_case_count": len(changed_cases),
        "changed_cases": changed_cases,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "id",
        "category",
        "input_text",
        "ai_response",
        "follow_up_question",
        "gentle_suggestion",
        "should_do",
        "should_avoid",
        "review_focus",
        "naturalness_1_5",
        "groundedness_1_5",
        "non_redundancy_1_5",
        "self_vs_other_correctness_1_5_or_na",
        "brevity_discipline_1_5",
        "follow_up_usefulness_1_5_or_na",
        "anti_template_feel_1_5",
        "reviewer_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            response = row.get("response", {})
            writer.writerow(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "input_text": row["input_text"],
                    "ai_response": response.get("ai_response"),
                    "follow_up_question": response.get("follow_up_question"),
                    "gentle_suggestion": response.get("gentle_suggestion"),
                    "should_do": row["should_do"],
                    "should_avoid": row["should_avoid"],
                    "review_focus": row["review_focus"],
                    "naturalness_1_5": "",
                    "groundedness_1_5": "",
                    "non_redundancy_1_5": "",
                    "self_vs_other_correctness_1_5_or_na": "",
                    "brevity_discipline_1_5": "",
                    "follow_up_usefulness_1_5_or_na": "",
                    "anti_template_feel_1_5": "",
                    "reviewer_notes": "",
                }
            )


def build_markdown_report(
    *,
    dataset_path: Path,
    run_name: str,
    selected_provider: str,
    summary: dict[str, Any],
    results: list[dict[str, Any]],
    comparison: dict[str, Any] | None,
) -> str:
    lines = [
        "# Response Quality Evaluation Report",
        "",
        f"- Run name: `{run_name}`",
        f"- Dataset: `{dataset_path}`",
        f"- Provider: `{selected_provider}`",
        f"- Generated at: `{datetime.now(UTC).isoformat()}`",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Successful cases: {summary['successful_cases']}",
        f"- Failed cases: {summary['failed_cases']}",
        f"- Average ai_response word count: {summary['average_word_count']}",
        "",
        "## Heuristic Flags",
        "",
    ]
    if summary["issue_counts"]:
        for issue, count in sorted(summary["issue_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{issue}`: {count}")
    else:
        lines.append("- No heuristic flags.")
    lines.extend(["", "## Repeated Openings", ""])
    if summary["repeated_openings"]:
        for opening, count in sorted(summary["repeated_openings"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{opening}`: {count}")
    else:
        lines.append("- No repeated openings crossed the threshold.")
    lines.extend(["", "## Repeated Questions", ""])
    if summary["repeated_questions"]:
        for question, count in sorted(summary["repeated_questions"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{question}`: {count}")
    else:
        lines.append("- No repeated question stems crossed the threshold.")
    lines.extend(["", "## Flagged Cases", ""])
    flagged = [result for result in results if result.get("issues")]
    if flagged:
        for result in flagged:
            response = result.get("response", {})
            lines.extend(
                [
                    f"### {result['id']} ({result['category']})",
                    "",
                    f"- Input: {result['input_text']}",
                    f"- Output: {response.get('ai_response')}",
                    f"- Issues: {', '.join(result['issues'])}",
                    f"- Review focus: {result['review_focus']}",
                    "",
                ]
            )
    else:
        lines.append("- No cases were flagged by the lightweight heuristics.")
    if comparison:
        lines.extend(["", "## Baseline Comparison", ""])
        lines.append(f"- Changed cases: {comparison['changed_case_count']}")
        for change in comparison["changed_cases"][:20]:
            lines.extend(
                [
                    f"### {change['id']} ({change['category']})",
                    "",
                    f"- Before: {change['before']}",
                    f"- After: {change['after']}",
                    f"- Word count delta: {change['word_count_delta']}",
                    f"- Issue delta: {change['issue_delta']}",
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    args = parse_args()
    dataset_path = args.dataset.resolve()
    cases = load_dataset(dataset_path)
    selected_cases = select_cases(cases, limit=args.limit, category=args.category, case_id=args.case_id)
    if not selected_cases:
        raise SystemExit("No evaluation cases matched the requested filters.")

    run_name = args.run_name or datetime.now(UTC).strftime("response-quality-%Y%m%dT%H%M%SZ")
    run_dir = args.output_dir.resolve() / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    selected_provider = get_response_provider_name(args.provider or None)
    results = [_safe_run_case(case, provider_override=args.provider or None) for case in selected_cases]
    summary = summarize(results)
    baseline_payload = _load_baseline(args.baseline)
    if baseline_payload is not None:
        baseline_payload.setdefault("metadata", {})
        baseline_payload["metadata"]["source_path"] = str(args.baseline.resolve())
    comparison = compare_against_baseline(results, baseline_payload)

    results_payload = {
        "metadata": {
            "run_name": run_name,
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset_path": str(dataset_path),
            "provider": selected_provider,
            "provider_override": args.provider or None,
            "case_count": len(results),
        },
        "summary": summary,
        "comparison": comparison,
        "results": results,
    }

    write_json(run_dir / "results.json", results_payload)
    write_jsonl(run_dir / "responses.jsonl", results)
    write_review_csv(run_dir / "review_template.csv", results)
    report_text = build_markdown_report(
        dataset_path=dataset_path,
        run_name=run_name,
        selected_provider=selected_provider,
        summary=summary,
        results=results,
        comparison=comparison,
    )
    (run_dir / "report.md").write_text(report_text, encoding="utf-8")
    print(f"Wrote response quality eval artifacts to {run_dir}")


if __name__ == "__main__":
    main()
