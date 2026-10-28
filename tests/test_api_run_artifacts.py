import json

import api_benchmark


def test_api_benchmark_writes_results_summary_and_html(tmp_path, monkeypatch):
    cases = tmp_path / "cases.jsonl"
    cases.write_text(
        json.dumps({
            "id": "hello",
            "prompt": "Say hello",
            "expected_substring": "hello",
            "forbidden_substrings": ["unsafe"],
            "category": "greeting",
            "severity": "low",
        }) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(api_benchmark, "api_completion", lambda *args, **kwargs: "Hello there")
    output = tmp_path / "output"
    summary = api_benchmark.run_api_benchmark(
        "fake-model", str(cases), "https://example.test/v1", "dummy-key",
        output=str(output), max_new_tokens=16,
    )
    payload = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert summary["total"] == 1
    assert summary["quality_gate"]["passed"] is True
    assert summary["category_scores"]["greeting"]["cases"] == 1
    assert (output / "report.html").exists()
    assert payload["cases"][0]["severity"] == "low"
    assert payload["quality_gate"]["passed"] is True
    assert "dummy-key" not in (output / "results.json").read_text(encoding="utf-8")
