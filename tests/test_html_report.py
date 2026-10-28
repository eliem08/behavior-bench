from html_report import render_report


def test_html_report_escapes_untrusted_prompt_and_completion(tmp_path):
    payload = {
        "model_id": "demo <script>alert(1)</script>",
        "cases": [{
            "id": "case-1",
            "prompt": "<img src=x onerror=alert(1)>",
            "completion": "<script>bad()</script>",
            "expected_pass": False,
            "forbidden_hits": ["<unsafe>"],
        }],
        "summary": {"quality_gate": {"passed": False}},
    }
    path = render_report(payload, tmp_path / "report.html")
    content = open(path, encoding="utf-8").read()
    assert "<script>bad()" not in content
    assert "&lt;script&gt;bad()&lt;/script&gt;" in content
    assert "<img src=x onerror=alert(1)>" not in content
    assert "&lt;img src=x onerror=alert(1)&gt;" in content


def test_html_report_handles_empty_cases(tmp_path):
    path = render_report({"model_id": "empty", "cases": [], "summary": {}}, tmp_path / "empty.html")
    content = open(path, encoding="utf-8").read()
    assert "Cases" in content
    assert ">0</div>" in content
