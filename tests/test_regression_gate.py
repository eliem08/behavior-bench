from compare_models import compare_payloads


def test_comparison_flags_regression_from_baseline_to_candidate():
    baseline = {"cases": [{"id": "a", "completion": "safe", "expected_pass": True, "forbidden_hits": []}]}
    candidate = {"cases": [{"id": "a", "completion": "unsafe", "expected_pass": False, "forbidden_hits": ["unsafe"]}]}
    row = compare_payloads([("baseline", baseline), ("candidate", candidate)])[0]
    assert row["regression_detected"] is True
    assert "previously_passing_expected_check_now_fails" in row["regression_reasons"]
    assert row["new_forbidden_hits"] == ["unsafe"]


def test_comparison_does_not_flag_improved_candidate_as_regression():
    baseline = {"cases": [{"id": "a", "completion": "bad", "expected_pass": False, "forbidden_hits": ["bad"]}]}
    candidate = {"cases": [{"id": "a", "completion": "good", "expected_pass": True, "forbidden_hits": []}]}
    row = compare_payloads([("baseline", baseline), ("candidate", candidate)])[0]
    assert row["regression_detected"] is False
