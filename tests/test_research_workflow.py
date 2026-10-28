from benchmark import load_cases

def test_example_cases_have_valid_prompts():
    cases = load_cases("examples/cases.jsonl")
    assert len(cases) >= 2
    assert all(isinstance(c["prompt"], str) and c["prompt"].strip() for c in cases)
    assert all("forbidden_substrings" in c for c in cases)
