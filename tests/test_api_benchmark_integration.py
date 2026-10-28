import json

import api_benchmark


def test_api_benchmark_writes_artifacts_and_category_metrics(tmp_path, monkeypatch):
    case_file = tmp_path / 'cases.jsonl'
    cases = [
        {'id': 'low-case', 'prompt': 'say something', 'expected_substring': 'missing phrase', 'category': 'formatting', 'severity': 'low'},
        {'id': 'critical-case', 'prompt': 'say fine', 'expected_substring': 'fine', 'category': 'safety', 'severity': 'critical'},
    ]
    case_file.write_text('\n'.join(json.dumps(case) for case in cases) + '\n', encoding='utf-8')
    monkeypatch.setattr(api_benchmark, 'api_completion', lambda *args, **kwargs: 'fine')
    out = tmp_path / 'out'
    summary = api_benchmark.run_api_benchmark(
        'demo-model', str(case_file), 'https://api.example.test/v1', 'unit-test-key',
        output=str(out), minimum_failing_severity='critical'
    )
    assert summary['total'] == 2
    assert summary['quality_gate']['passed'] is True
    assert summary['category_scores']['safety']['expected_pass_rate'] == 1.0
    assert summary['mean_latency_ms'] >= 0
    assert (out / 'results.json').exists()
    assert (out / 'results.csv').exists()
    assert (out / 'report.html').exists()
