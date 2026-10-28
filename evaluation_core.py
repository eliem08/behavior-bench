"""Dependency-light case schema validation and transparent quality gates."""
import json
from pathlib import Path


def load_cases(path):
    cases = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(case, dict):
            raise ValueError(f"Line {line_number} must be a JSON object")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"Line {line_number} needs a non-empty string prompt")
        case.setdefault("id", f"case-{len(cases)+1:03d}")
        if not isinstance(case["id"], str) or not case["id"].strip():
            raise ValueError(f"Line {line_number} needs a non-empty string id")
        if "expected_substring" in case and case["expected_substring"] is not None and not isinstance(case["expected_substring"], str):
            raise ValueError(f"Line {line_number}: expected_substring must be a string")
        case.setdefault("forbidden_substrings", [])
        if not isinstance(case["forbidden_substrings"], list) or not all(isinstance(s, str) for s in case["forbidden_substrings"]):
            raise ValueError(f"Line {line_number}: forbidden_substrings must be a list of strings")
        case.setdefault("category", "uncategorized")
        case.setdefault("severity", "normal")
        for field in ("category", "severity"):
            if not isinstance(case[field], str) or not case[field].strip():
                raise ValueError(f"Line {line_number}: {field} must be a non-empty string")
        if case["severity"].casefold() not in SEVERITY_ORDER:
            raise ValueError(f"Line {line_number}: severity must be low, normal, high, or critical")
        case["severity"] = case["severity"].casefold()
        cases.append(case)
    if not cases:
        raise ValueError("Case file contains no test cases")
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Case IDs must be unique")
    return cases


SEVERITY_ORDER = {"low": 0, "normal": 1, "high": 2, "critical": 3}


def assess_quality_gate(rows, minimum_failing_severity=None):
    """Return transparent regression findings; substring checks are not semantic evaluation.

    When a minimum severity is supplied, only findings at that severity or above
    fail the gate. All findings remain visible in the returned diagnostic list.
    """
    if minimum_failing_severity is not None and minimum_failing_severity not in SEVERITY_ORDER:
        raise ValueError("minimum_failing_severity must be low, normal, high, or critical")
    findings = []
    for row in rows:
        metadata = {
            "case_id": row["id"],
            "category": row.get("category", "uncategorized"),
            "severity": row.get("severity", "normal"),
        }
        if row.get("expected_pass") is False:
            findings.append({**metadata, "reason": "expected_substring_missing"})
        if row.get("forbidden_hits"):
            findings.append({**metadata, "reason": "forbidden_substring_found",
                             "matches": row["forbidden_hits"]})
    failures = findings
    if minimum_failing_severity is not None:
        threshold = SEVERITY_ORDER[minimum_failing_severity]
        failures = [item for item in findings if SEVERITY_ORDER.get(item["severity"], 1) >= threshold]
    return {
        "passed": not failures,
        "failure_count": len(failures),
        "total_finding_count": len(findings),
        "minimum_failing_severity": minimum_failing_severity,
        "failures": failures,
        "all_findings": findings,
    }
