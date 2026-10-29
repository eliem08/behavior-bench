import json

import pytest

from evaluation_core import assess_quality_gate, evaluate_structured_output, load_cases


def test_structured_output_checks_required_nested_keys_and_expected_subset():
    result = evaluate_structured_output(
        '{"status":"ok","data":{"count":3,"items":["a"]}}',
        expected_json={"status": "ok", "data": {"count": 3}},
        required_json_keys=["status", "data.count", "data.items"],
    )
    assert result == {"structured_pass": True, "structured_errors": []}


def test_structured_output_reports_missing_keys_and_wrong_values():
    result = evaluate_structured_output(
        '{"status":"ok","data":{"count":"3"}}',
        expected_json={"status": "ok", "data": {"count": 3}},
        required_json_keys=["data.items"],
    )
    assert result["structured_pass"] is False
    assert any("required key missing" in error for error in result["structured_errors"])
    assert any("value mismatch" in error for error in result["structured_errors"])


def test_structured_output_rejects_invalid_json():
    result = evaluate_structured_output("not json", required_json_keys=["status"])
    assert result["structured_pass"] is False
    assert "not valid JSON" in result["structured_errors"][0]


def test_structured_output_is_not_checked_when_not_configured():
    assert evaluate_structured_output("plain text") == {
        "structured_pass": None, "structured_errors": []
    }


def test_structured_failure_trips_quality_gate():
    result = assess_quality_gate([{
        "id": "json-case", "category": "format", "severity": "high",
        "expected_pass": None, "forbidden_hits": [],
        "structured_pass": False, "structured_errors": ["$.status: required key missing"],
    }])
    assert result["passed"] is False
    assert result["failures"][0]["reason"] == "structured_output_invalid"


def test_case_schema_validates_structured_expectations(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps({
        "prompt": "Return JSON", "expected_json": {"status": "ok"},
        "required_json_keys": ["status", "data.count"],
    }), encoding="utf-8")
    cases = load_cases(path)
    assert cases[0]["expected_json"] == {"status": "ok"}
    assert cases[0]["required_json_keys"] == ["status", "data.count"]

    path.write_text(json.dumps({"prompt": "Return JSON", "required_json_keys": "status"}), encoding="utf-8")
    with pytest.raises(ValueError, match="required_json_keys"):
        load_cases(path)
