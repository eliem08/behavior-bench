from compare_models import compare_payloads


def test_missing_baseline_case_in_candidate_is_regression():
    baseline = {"cases": [{"id": "a", "completion": "ok", "expected_pass": True, "forbidden_hits": []}]}
    candidate = {"cases": []}
    row = compare_payloads([("baseline", baseline), ("candidate", candidate)])[0]
    assert row["regression_detected"] is True
    assert row["regression_reasons"] == ["case_missing_from_candidate"]


def test_case_only_in_candidate_is_not_regression():
    baseline = {"cases": []}
    candidate = {"cases": [{"id": "new", "completion": "new", "expected_pass": True, "forbidden_hits": []}]}
    row = compare_payloads([("baseline", baseline), ("candidate", candidate)])[0]
    assert row["regression_detected"] is False
