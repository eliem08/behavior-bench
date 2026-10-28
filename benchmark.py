"""Run reproducible prompt regression cases against a causal language model.

Input JSONL rows accept: id, prompt, expected_substring (optional), forbidden_substrings (optional list).
This is a lightweight regression harness, not a comprehensive quality or safety evaluation.
"""
from __future__ import annotations
import argparse, json, hashlib, csv, sys
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from provenance import build_manifest
from html_report import render_report
from evaluation_core import load_cases, assess_quality_gate

def run_benchmark(model_id, cases_path, output="outputs/benchmark", max_new_tokens=96, device="auto", minimum_failing_severity=None):
    device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "mps" if getattr(torch.backends,"mps",None) and torch.backends.mps.is_available() else "cpu")
    cases = load_cases(cases_path)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto").to(device).eval()
    rows=[]
    for case in cases:
        inputs=tokenizer(case["prompt"], return_tensors="pt").to(device)
        started = time.perf_counter()
        with torch.inference_mode():
            generated=model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tokenizer.eos_token_id)
        latency_ms = (time.perf_counter() - started) * 1000
        completion_tokens = int(generated.shape[1] - inputs["input_ids"].shape[1])
        completion=tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        expected=case.get("expected_substring")
        forbidden=case.get("forbidden_substrings", [])
        rows.append({"id":case["id"],"category":case["category"],"severity":case["severity"],"prompt":case["prompt"],"completion":completion,"expected_substring":expected or "",
          "expected_pass": None if not expected else expected.casefold() in completion.casefold(),
          "forbidden_hits":[s for s in forbidden if s.casefold() in completion.casefold()],
          "completion_sha256":hashlib.sha256(completion.encode()).hexdigest(),
          "input_tokens":int(inputs["input_ids"].shape[1]),"completion_tokens":completion_tokens,"latency_ms":round(latency_ms, 3)})
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    (out/"results.json").write_text(json.dumps({"model_id":model_id,"device":device,"cases":rows,"manifest":build_manifest("behavior-bench",model_id=model_id,device=device,config={"max_new_tokens":max_new_tokens},inputs={"case_file":Path(cases_path).read_text(encoding="utf-8")})},indent=2,ensure_ascii=False),encoding="utf-8")
    with (out/"results.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["id","category","severity","prompt","completion","expected_substring","expected_pass","forbidden_hits","completion_sha256","input_tokens","completion_tokens","latency_ms"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:
            r2=dict(r);r2["forbidden_hits"]="; ".join(r["forbidden_hits"]);w.writerow(r2)
    checked=[r for r in rows if r["expected_pass"] is not None]
    gate = assess_quality_gate(rows, minimum_failing_severity)
    summary={"model_id":model_id,"device":device,"manifest":build_manifest("behavior-bench",model_id=model_id,device=device,config={"max_new_tokens":max_new_tokens, "minimum_failing_severity":minimum_failing_severity}),"total":len(rows),"expected_checks":len(checked),"expected_pass_rate":sum(bool(r["expected_pass"]) for r in checked)/len(checked) if checked else None,"cases_with_forbidden_hits":sum(bool(r["forbidden_hits"]) for r in rows),"quality_gate":gate,"output":str(out)}
    category_scores = {}
    for category in sorted({r["category"] for r in rows}):
        group = [r for r in rows if r["category"] == category]
        group_checked = [r for r in group if r["expected_pass"] is not None]
        category_scores[category] = {
            "cases": len(group),
            "expected_checks": len(group_checked),
            "expected_pass_rate": sum(bool(r["expected_pass"]) for r in group_checked) / len(group_checked) if group_checked else None,
            "cases_with_forbidden_hits": sum(bool(r["forbidden_hits"]) for r in group),
            "mean_latency_ms": round(sum(r["latency_ms"] for r in group) / len(group), 3) if group else None,
        }
    summary["category_scores"] = category_scores
    summary["mean_latency_ms"] = round(sum(r["latency_ms"] for r in rows) / len(rows), 3) if rows else None
    summary["total_input_tokens"] = sum(r["input_tokens"] for r in rows)
    summary["total_completion_tokens"] = sum(r["completion_tokens"] for r in rows)
    report_path = render_report({"model_id": model_id, "cases": rows, "summary": summary}, out / "report.html")
    summary["html_report"] = report_path
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-id",default="distilgpt2");p.add_argument("--cases",default="examples/cases.jsonl")
    p.add_argument("--output",default="outputs/benchmark");p.add_argument("--max-new-tokens",type=int,default=96)
    p.add_argument("--device",choices=["auto","cuda","mps","cpu"],default="auto")
    p.add_argument("--fail-on-regression",action="store_true",help="Exit with status 1 if any expected or forbidden substring check fails")
    p.add_argument("--minimum-failing-severity",choices=["low","normal","high","critical"],default=None,help="Only fail on findings at this severity or higher; implies --fail-on-regression")
    a=p.parse_args()
    summary=run_benchmark(a.model_id,a.cases,a.output,a.max_new_tokens,a.device,a.minimum_failing_severity)
    print(json.dumps(summary,indent=2))
    if (a.fail_on_regression or a.minimum_failing_severity is not None) and not summary["quality_gate"]["passed"]:
        sys.exit(1)
if __name__=="__main__":main()
