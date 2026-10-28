"""Compare saved Behavior Bench results without re-running models.

Example:
  python compare_models.py --results outputs/model-a/results.json outputs/model-b/results.json
"""
from __future__ import annotations
import argparse
import json
import csv
from pathlib import Path

def compare_payloads(named_payloads):
    """Compare already-computed results keyed by case ID."""
    indexed = {}
    for name, payload in named_payloads:
        for row in payload.get("cases", []):
            indexed.setdefault(row["id"], {})[name] = row
    comparisons = []
    for case_id, by_model in sorted(indexed.items()):
        names = sorted(by_model)
        item = {"id": case_id, "models_present": names}
        for name in names:
            row = by_model[name]
            item[f"{name}_completion"] = row.get("completion", "")
            item[f"{name}_expected_pass"] = row.get("expected_pass")
            item[f"{name}_forbidden_hits"] = row.get("forbidden_hits", [])
        if len(names) >= 2:
            a, b = names[:2]
            item["outputs_identical"] = by_model[a].get("completion") == by_model[b].get("completion")
            item["expected_pass_changed"] = by_model[a].get("expected_pass") != by_model[b].get("expected_pass")
        comparisons.append(item)
    return comparisons

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", nargs="+", required=True, help="Paths to results.json; use --labels to name each")
    p.add_argument("--labels", nargs="*", default=None)
    p.add_argument("--output", default="outputs/model-comparison")
    a = p.parse_args()
    if a.labels and len(a.labels) != len(a.results):
        p.error("--labels must have the same number of values as --results")
    loaded = []
    for i, path in enumerate(a.results):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        label = a.labels[i] if a.labels else payload.get("model_id", Path(path).parent.name)
        loaded.append((label, payload))
    rows = compare_payloads(loaded)
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.json").write_text(json.dumps({"inputs": a.results, "models": [n for n, _ in loaded], "cases": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    columns = sorted({key for row in rows for key in row if not isinstance(row[key], (list, dict))})
    with (out / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns); writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in columns})
    print(json.dumps({"models": [n for n, _ in loaded], "cases_compared": len(rows), "output": str(out)}, indent=2))

if __name__ == "__main__":
    main()
