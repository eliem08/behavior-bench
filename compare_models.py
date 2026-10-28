"""Compare saved Behavior Bench results without re-running models.

Example:
  python compare_models.py --results outputs/model-a/results.json outputs/model-b/results.json
"""
from __future__ import annotations
import argparse
import json
import csv
import sys
from pathlib import Path
from html_report import render_report

def compare_payloads(named_payloads):
    """Compare already-computed results keyed by case ID."""
    indexed = {}
    for name, payload in named_payloads:
        for row in payload.get("cases", []):
            indexed.setdefault(row["id"], {})[name] = row
    baseline_name = named_payloads[0][0] if named_payloads else None
    candidate_name = named_payloads[1][0] if len(named_payloads) > 1 else None
    comparisons = []
    for case_id, by_model in sorted(indexed.items()):
        names = list(by_model)
        item = {"id": case_id, "models_present": names}
        for name in names:
            row = by_model[name]
            item[f"{name}_completion"] = row.get("completion", "")
            item[f"{name}_expected_pass"] = row.get("expected_pass")
            item[f"{name}_forbidden_hits"] = row.get("forbidden_hits", [])
        reasons = []
        if baseline_name and candidate_name and baseline_name in by_model:
            if candidate_name not in by_model:
                item["outputs_identical"] = False
                item["expected_pass_changed"] = False
                item["new_forbidden_hits"] = []
                reasons.append("case_missing_from_candidate")
            else:
                baseline, candidate = by_model[baseline_name], by_model[candidate_name]
                item["outputs_identical"] = baseline.get("completion") == candidate.get("completion")
                item["expected_pass_changed"] = baseline.get("expected_pass") != candidate.get("expected_pass")
                if baseline.get("expected_pass") is True and candidate.get("expected_pass") is False:
                    reasons.append("previously_passing_expected_check_now_fails")
                new_forbidden = sorted(set(candidate.get("forbidden_hits", [])) - set(baseline.get("forbidden_hits", [])))
                if new_forbidden:
                    reasons.append("new_forbidden_substring_hits")
                item["new_forbidden_hits"] = new_forbidden
        else:
            item["new_forbidden_hits"] = []
        item["regression_reasons"] = reasons
        item["regression_detected"] = bool(reasons)
        comparisons.append(item)
    return comparisons

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", nargs="+", required=True, help="Paths to results.json; use --labels to name each")
    p.add_argument("--labels", nargs="*", default=None)
    p.add_argument("--output", default="outputs/model-comparison")
    p.add_argument("--fail-on-regression", action="store_true", help="Exit with status 1 if candidate regresses against baseline; first input is baseline, second is candidate")
    a = p.parse_args()
    if a.labels and len(a.labels) != len(a.results):
        p.error("--labels must have the same number of values as --results")
    loaded = []
    for i, path in enumerate(a.results):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        label = a.labels[i] if a.labels else payload.get("model_id", Path(path).parent.name)
        loaded.append((label, payload))
    labels = [name for name, _ in loaded]
    if len(labels) != len(set(labels)):
        p.error("Model labels must be unique")
    rows = compare_payloads(loaded)
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    payload = {"inputs": a.results, "models": labels, "baseline": loaded[0][0], "candidate": loaded[1][0] if len(loaded) > 1 else None, "regressions": [row for row in rows if row["regression_detected"]], "cases": rows}
    (out / "comparison.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_rows = []
    candidate_name = payload["candidate"]
    for row in rows:
        item = dict(row)
        item["completion"] = row.get(f"{candidate_name}_completion", "") if candidate_name else ""
        item["forbidden_hits"] = row.get(f"{candidate_name}_forbidden_hits", row.get("new_forbidden_hits", []))
        report_rows.append(item)
    payload["cases"] = report_rows
    render_report(payload, out / "report.html")
    columns = sorted({key for row in rows for key in row if not isinstance(row[key], (list, dict))})
    with (out / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns); writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in columns})
    result = {"models": [n for n, _ in loaded], "cases_compared": len(rows), "regression_count": len(payload["regressions"]), "output": str(out)}
    print(json.dumps(result, indent=2))
    if a.fail_on_regression and result["regression_count"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
