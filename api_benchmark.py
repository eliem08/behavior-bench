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
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from benchmark import load_cases, assess_quality_gate
from provenance import build_manifest


def api_completion(prompt, base_url, model_id, api_key, max_new_tokens=96, timeout=90):
    parsed = urlsplit(base_url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError("base_url must be an absolute http:// or https:// URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("base_url must not contain credentials, query parameters, or a fragment")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Use HTTPS for remote API endpoints; plain HTTP is allowed only for localhost")
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_new_tokens,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not include request headers or secrets in raised messages.
        raise RuntimeError(f"API returned HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"API connection failed: {exc.reason}") from None
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ValueError("API response did not contain choices[0].message.content") from None
    if not isinstance(text, str):
        raise ValueError("API completion content must be a string")
    return text


def run_api_benchmark(model_id, cases_path, base_url, api_key, output="outputs/api-benchmark", max_new_tokens=96):
    cases = load_cases(cases_path)
    rows = []
    for case in cases:
        completion = api_completion(case["prompt"], base_url, model_id, api_key, max_new_tokens)
        expected = case.get("expected_substring")
        forbidden = case.get("forbidden_substrings", [])
        rows.append({
            "id": case["id"],
            "prompt": case["prompt"],
            "completion": completion,
            "expected_substring": expected or "",
            "expected_pass": None if not expected else expected.casefold() in completion.casefold(),
            "forbidden_hits": [s for s in forbidden if s.casefold() in completion.casefold()],
            "completion_sha256": hashlib.sha256(completion.encode("utf-8")).hexdigest(),
        })
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    gate = assess_quality_gate(rows)
    manifest = build_manifest(
        "behavior-bench", model_id=model_id, device="api",
        config={"max_new_tokens": max_new_tokens, "base_url": base_url},
        inputs={"case_file": Path(cases_path).read_text(encoding="utf-8")},
    )
    payload = {
        "model_id": model_id, "provider": "openai-compatible", "device": "api",
        "cases": rows, "manifest": manifest,
        "warning": "Substring checks are regression signals, not semantic evaluation.",
    }
    (out / "results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["id", "prompt", "completion", "expected_substring", "expected_pass", "forbidden_hits", "completion_sha256"]
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
    args = parser.parse_args()
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        parser.error(f"Set the API key in environment variable {args.api_key_env}")
    summary = run_api_benchmark(args.model_id, args.cases, args.base_url, api_key, args.output, args.max_new_tokens)
    print(json.dumps(summary, indent=2))
    if args.fail_on_regression and not summary["quality_gate"]["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
