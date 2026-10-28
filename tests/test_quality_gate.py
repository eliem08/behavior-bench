import json
import pytest
from benchmark import assess_quality_gate, load_cases


def test_quality_gate_passes_when_checks_pass():
    rows = [{"id": "ok", "expected_pass": True, "forbidden_hits": []}]
    result = assess_quality_gate(rows)
    assert result["passed"] is True
    assert result["failure_count"] == 0


def test_quality_gate_reports_expected_and_forbidden_failures():
    rows = [
        {"id": "missing", "expected_pass": False, "forbidden_hits": []},
        {"id": "forbidden", "expected_pass": None, "forbidden_hits": ["secret"]},
    ]
    result = assess_quality_gate(rows)
    assert result["passed"] is False
    assert result["failure_count"] == 2
    assert {item["reason"] for item in result["failures"]} == {
        "expected_substring_missing", "forbidden_substring_found"
    }


def test_load_cases_rejects_duplicate_ids(tmp_path):
    p = tmp_path / "cases.jsonl"
    p.write_text(
        json.dumps({"id": "same", "prompt": "first"}) + "\n" +
        json.dumps({"id": "same", "prompt": "second"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unique"):
        load_cases(p)


def test_load_cases_reports_bad_json_line(tmp_path):
    p = tmp_path / "cases.jsonl"
    p.write_text('{"prompt":"ok"}\n{bad json}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        load_cases(p)


def test_load_cases_rejects_invalid_forbidden_substrings(tmp_path):
    p = tmp_path / "cases.jsonl"
    p.write_text(json.dumps({"prompt": "hello", "forbidden_substrings": "not-a-list"}), encoding="utf-8")
    with pytest.raises(ValueError, match="list of strings"):
        load_cases(p)


def test_load_cases_defaults_and_validates_category_and_severity(tmp_path):
    p = tmp_path / "cases.jsonl"
    p.write_text(json.dumps({"prompt": "hello", "category": "factuality", "severity": "high"}), encoding="utf-8")
    cases = load_cases(p)
    assert cases[0]["category"] == "factuality"
    assert cases[0]["severity"] == "high"
    p.write_text(json.dumps({"prompt": "hello", "severity": ""}), encoding="utf-8")
    with pytest.raises(ValueError, match="severity"):
        load_cases(p)


def test_severity_threshold_only_fails_at_or_above_threshold():
    from evaluation_core import assess_quality_gate

    rows = [
        {"id": "low-case", "category": "style", "severity": "low", "expected_pass": False, "forbidden_hits": []},
        {"id": "high-case", "category": "safety", "severity": "high", "expected_pass": False, "forbidden_hits": []},
    ]
    result = assess_quality_gate(rows, minimum_failing_severity="high")
    assert result["passed"] is False
    assert result["failure_count"] == 1
    assert result["failures"][0]["case_id"] == "high-case"
    assert result["total_finding_count"] == 2


def test_severity_threshold_can_allow_low_severity_findings():
    from evaluation_core import assess_quality_gate

    rows = [{"id": "low-case", "severity": "low", "expected_pass": False, "forbidden_hits": []}]
    result = assess_quality_gate(rows, minimum_failing_severity="high")
    assert result["passed"] is True
    assert result["failure_count"] == 0
    assert result["total_finding_count"] == 1
