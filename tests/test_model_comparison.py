from compare_models import compare_payloads

def test_compare_payloads_aligns_cases_and_flags_changed_results():
    left = {"cases": [{"id": "a", "completion": "yes", "expected_pass": True, "forbidden_hits": []}]}
    right = {"cases": [{"id": "a", "completion": "no", "expected_pass": False, "forbidden_hits": ["no"]}]}
    rows = compare_payloads([("left", left), ("right", right)])
    assert len(rows) == 1
    assert rows[0]["outputs_identical"] is False
    assert rows[0]["expected_pass_changed"] is True

def test_compare_payloads_keeps_cases_missing_from_one_run():
    rows = compare_payloads([("one", {"cases": [{"id": "a", "completion": "x"}]}), ("two", {"cases": []})])
    assert rows[0]["models_present"] == ["one"]

def test_compare_payloads_flags_structured_output_regression():
    left = {"cases": [{
        "id": "json", "completion": '{"status":"ok"}',
        "structured_pass": True, "structured_errors": [],
    }]}
    right = {"cases": [{
        "id": "json", "completion": '{"status":',
        "structured_pass": False,
        "structured_errors": ["output is not valid JSON"],
    }]}
    row = compare_payloads([("baseline", left), ("candidate", right)])[0]
    assert row["structured_pass_changed"] is True
    assert row["new_structured_errors"] == ["output is not valid JSON"]
    assert "previously_valid_structured_output_now_fails" in row["regression_reasons"]
    assert row["regression_detected"] is True
