import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from careroute.agent import run_triage

EVALS_DIR = Path(__file__).resolve().parent
MAX_TOKENS = 1024


def extract_urgency(summary: str) -> str | None:
    match = re.search(
        r"urgency level\W+(emergency|urgent|routine|self[\s_-]?care)", summary.lower()
    )
    if not match:
        return None
    return re.sub(r"[\s-]", "_", match.group(1))


def run_case(case: dict) -> dict:
    record = {
        "id": case["id"],
        "expected_urgency": case["expected_urgency"],
        "actual_urgency": None,
        "urgency_ok": False,
        "tools_ok": False,
        "passed": False,
        "error": None,
    }
    try:
        result = run_triage(case["input"], max_tokens=MAX_TOKENS)
        called = [c["name"] for c in result["tool_calls"]]
        actual = extract_urgency(result["summary"])
        if case["expected_urgency"] == "clarify":
            record["actual_urgency"] = actual or "clarify"
            record["urgency_ok"] = actual is None and "?" in result["summary"]
            record["tools_ok"] = "score_urgency" not in called
        else:
            record["actual_urgency"] = actual
            record["urgency_ok"] = actual == case["expected_urgency"]
            record["tools_ok"] = all(t in called for t in case["expected_tools"])
        record["passed"] = record["urgency_ok"] and record["tools_ok"]
        record["tool_calls"] = called
        record["summary"] = result["summary"]
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    return record


def print_table(records: list[dict]) -> None:
    header = f"{'case':<32} {'expected':<10} {'actual':<10} {'urgency':<8} {'tools':<6} {'result'}"
    print(header)
    print("-" * len(header))
    for r in records:
        if r["error"]:
            print(f"{r['id']:<32} {r['expected_urgency']:<10} {'ERROR':<10} {'-':<8} {'-':<6} {r['error']}")
        else:
            print(
                f"{r['id']:<32} {r['expected_urgency']:<10} {str(r['actual_urgency']):<10} "
                f"{'ok' if r['urgency_ok'] else 'FAIL':<8} {'ok' if r['tools_ok'] else 'FAIL':<6} "
                f"{'PASS' if r['passed'] else 'FAIL'}"
            )
    passed = sum(1 for r in records if r["passed"])
    print("-" * len(header))
    print(f"accuracy: {passed}/{len(records)} ({passed / len(records):.0%})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    cases = json.loads((EVALS_DIR / "cases.json").read_text())
    if args.limit:
        cases = cases[: args.limit]

    records = [run_case(case) for case in cases]
    print_table(records)

    passed = sum(1 for r in records if r["passed"])
    (EVALS_DIR / "results.json").write_text(
        json.dumps({"accuracy": passed / len(records), "results": records}, indent=2)
    )


if __name__ == "__main__":
    main()
