"""Evaluate JSONL cases against an OpenAI-compatible chat-completions API.

Set the API key in an environment variable. The key is never written to result files.
This runner targets OpenAI-compatible endpoints; provider-specific options may vary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from evaluation_core import load_cases, assess_quality_gate, evaluate_structured_output
from provenance import build_manifest
from html_report import render_report


def api_completion(prompt, base_url, model_id, api_key, max_new_tokens=96, timeout=90, system_prompt=None, max_retries=2):
    """Call a chat-completions endpoint, retrying only transient HTTP failures.

    Retries are bounded to avoid runaway CI jobs. Authentication, validation,
    and other non-transient HTTP errors fail immediately.
    """
    parsed = urlsplit(base_url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError("base_url must be an absolute http:// or https:// URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("base_url must not contain credentials, query parameters, or a fragment")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Use HTTPS for remote API endpoints; plain HTTP is allowed only for localhost")
    if isinstance(max_retries, bool) or not isinstance(max_retries, int) or not 0 <= max_retries <= 5:
        raise ValueError("max_retries must be an integer from 0 to 5")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    url = base_url.rstrip("/") + "/chat/completions"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_new_tokens,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt >= max_retries:
                # Do not include request headers, response bodies, or secrets in raised messages.
                raise RuntimeError(f"API returned HTTP {exc.code}") from None
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = min(5.0, max(0.0, float(retry_after))) if retry_after is not None else min(2.0, 0.25 * (2 ** attempt))
            except (TypeError, ValueError):
                delay = min(2.0, 0.25 * (2 ** attempt))
            time.sleep(delay)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"API connection failed: {exc.reason}") from None
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ValueError("API response did not contain choices[0].message.content") from None
    if not isinstance(text, str):
        raise ValueError("API completion content must be a string")
    return text

def run_api_benchmark(model_id, cases_path, base_url, api_key, output="outputs/api-benchmark", max_new_tokens=96, minimum_failing_severity=None):
    cases = load_cases(cases_path)
    rows = []
    for case in cases:
        started = time.perf_counter()
        completion = api_completion(case["prompt"], base_url, model_id, api_key, max_new_tokens)
        latency_ms = (time.perf_counter() - started) * 1000
        expected = case.get("expected_substring")
        forbidden = case.get("forbidden_substrings", [])
        rows.append({
            "id": case["id"],
            "category": case["category"],
            "severity": case["severity"],
            "prompt": case["prompt"],
            "completion": completion,
            "expected_substring": expected or "",
            "expected_pass": None if not expected else expected.casefold() in completion.casefold(),
            "forbidden_hits": [s for s in forbidden if s.casefold() in completion.casefold()],
            **evaluate_structured_output(completion, case.get("expected_json"), case.get("required_json_keys")),
            "completion_sha256": hashlib.sha256(completion.encode("utf-8")).hexdigest(),
            "latency_ms": round(latency_ms, 3),
        })
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    gate = assess_quality_gate(rows, minimum_failing_severity)
    manifest = build_manifest(
        "behavior-bench", model_id=model_id, device="api",
        config={"max_new_tokens": max_new_tokens, "base_url": base_url, "minimum_failing_severity": minimum_failing_severity},
        inputs={"case_file": Path(cases_path).read_text(encoding="utf-8")},
    )
    payload = {
        "model_id": model_id, "provider": "openai-compatible", "device": "api",
        "cases": rows, "manifest": manifest,
        "warning": "Substring checks are regression signals, not semantic evaluation.",
    }
    (out / "results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["id", "category", "severity", "prompt", "completion", "expected_substring", "expected_pass", "forbidden_hits", "structured_pass", "structured_errors", "completion_sha256", "latency_ms"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            item = dict(row)
            item["forbidden_hits"] = "; ".join(row["forbidden_hits"])
            writer.writerow(item)
    checked = [row for row in rows if row["expected_pass"] is not None]
    summary = {
        "model_id": model_id, "provider": "openai-compatible", "device": "api",
        "manifest": manifest, "total": len(rows), "expected_checks": len(checked),
        "expected_pass_rate": sum(bool(row["expected_pass"]) for row in checked) / len(checked) if checked else None,
        "cases_with_forbidden_hits": sum(bool(row["forbidden_hits"]) for row in rows),
        "quality_gate": gate, "output": str(out),
    }
    category_scores = {}
    for category in sorted({row["category"] for row in rows}):
        group = [row for row in rows if row["category"] == category]
        group_checked = [row for row in group if row["expected_pass"] is not None]
        category_scores[category] = {
            "cases": len(group),
            "expected_checks": len(group_checked),
            "expected_pass_rate": sum(bool(row["expected_pass"]) for row in group_checked) / len(group_checked) if group_checked else None,
            "cases_with_forbidden_hits": sum(bool(row["forbidden_hits"]) for row in group),
            "mean_latency_ms": round(sum(row["latency_ms"] for row in group) / len(group), 3) if group else None,
        }
    summary["category_scores"] = category_scores
    summary["mean_latency_ms"] = round(sum(row["latency_ms"] for row in rows) / len(rows), 3) if rows else None
    payload["quality_gate"] = gate
    payload["summary"] = summary
    (out / "results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path = render_report({"model_id": model_id, "cases": rows, "summary": summary}, out / "report.html")
    summary["html_report"] = report_path
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="API root, for example https://api.example.com/v1")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Environment variable holding the API key")
    parser.add_argument("--cases", default="examples/cases.jsonl")
    parser.add_argument("--output", default="outputs/api-benchmark")
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--fail-on-regression", action="store_true")
    parser.add_argument("--minimum-failing-severity", choices=["low", "normal", "high", "critical"], default=None, help="Only fail on findings at this severity or higher; implies --fail-on-regression")
    args = parser.parse_args()
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        parser.error(f"Set the API key in environment variable {args.api_key_env}")
    summary = run_api_benchmark(args.model_id, args.cases, args.base_url, api_key, args.output, args.max_new_tokens, args.minimum_failing_severity)
    print(json.dumps(summary, indent=2))
    if (args.fail_on_regression or args.minimum_failing_severity is not None) and not summary["quality_gate"]["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
