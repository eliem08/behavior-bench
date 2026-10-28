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
