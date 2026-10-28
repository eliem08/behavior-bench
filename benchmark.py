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

def load_cases(path):
    cases = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(case, dict):
            raise ValueError(f"Line {line_number} must be a JSON object")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"Line {line_number} needs a non-empty string prompt")
        case.setdefault("id", f"case-{len(cases)+1:03d}")
        if not isinstance(case["id"], str) or not case["id"].strip():
            raise ValueError(f"Line {line_number} needs a non-empty string id")
        if "expected_substring" in case and case["expected_substring"] is not None and not isinstance(case["expected_substring"], str):
            raise ValueError(f"Line {line_number}: expected_substring must be a string")
        case.setdefault("forbidden_substrings", [])
        if not isinstance(case["forbidden_substrings"], list) or not all(isinstance(s, str) for s in case["forbidden_substrings"]):
            raise ValueError(f"Line {line_number}: forbidden_substrings must be a list of strings")
        cases.append(case)
    if not cases:
        raise ValueError("Case file contains no test cases")
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Case IDs must be unique")
    return cases


def assess_quality_gate(rows):
    """Return transparent regression findings; substring checks are not semantic evaluation."""
    failures = []
    for row in rows:
        if row["expected_pass"] is False:
            failures.append({"case_id": row["id"], "reason": "expected_substring_missing"})
        if row["forbidden_hits"]:
            failures.append({"case_id": row["id"], "reason": "forbidden_substring_found",
                             "matches": row["forbidden_hits"]})
    return {"passed": not failures, "failure_count": len(failures), "failures": failures}

def run_benchmark(model_id, cases_path, output="outputs/benchmark", max_new_tokens=96, device="auto"):
    device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "mps" if getattr(torch.backends,"mps",None) and torch.backends.mps.is_available() else "cpu")
    cases = load_cases(cases_path)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto").to(device).eval()
    rows=[]
    for case in cases:
        inputs=tokenizer(case["prompt"], return_tensors="pt").to(device)
        with torch.inference_mode():
            generated=model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tokenizer.eos_token_id)
        completion=tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        expected=case.get("expected_substring")
        forbidden=case.get("forbidden_substrings", [])
        rows.append({"id":case["id"],"prompt":case["prompt"],"completion":completion,"expected_substring":expected or "",
          "expected_pass": None if not expected else expected.casefold() in completion.casefold(),
          "forbidden_hits":[s for s in forbidden if s.casefold() in completion.casefold()],
          "completion_sha256":hashlib.sha256(completion.encode()).hexdigest()})
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    (out/"results.json").write_text(json.dumps({"model_id":model_id,"device":device,"cases":rows,"manifest":build_manifest("behavior-bench",model_id=model_id,device=device,config={"max_new_tokens":max_new_tokens},inputs={"case_file":Path(cases_path).read_text(encoding="utf-8")})},indent=2,ensure_ascii=False),encoding="utf-8")
    with (out/"results.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["id","prompt","completion","expected_substring","expected_pass","forbidden_hits","completion_sha256"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:
            r2=dict(r);r2["forbidden_hits"]="; ".join(r["forbidden_hits"]);w.writerow(r2)
    checked=[r for r in rows if r["expected_pass"] is not None]
    gate = assess_quality_gate(rows)
    summary={"model_id":model_id,"device":device,"manifest":build_manifest("behavior-bench",model_id=model_id,device=device,config={"max_new_tokens":max_new_tokens}),"total":len(rows),"expected_checks":len(checked),"expected_pass_rate":sum(bool(r["expected_pass"]) for r in checked)/len(checked) if checked else None,"cases_with_forbidden_hits":sum(bool(r["forbidden_hits"]) for r in rows),"quality_gate":gate,"output":str(out)}
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-id",default="distilgpt2");p.add_argument("--cases",default="examples/cases.jsonl")
    p.add_argument("--output",default="outputs/benchmark");p.add_argument("--max-new-tokens",type=int,default=96)
    p.add_argument("--device",choices=["auto","cuda","mps","cpu"],default="auto")
    p.add_argument("--fail-on-regression",action="store_true",help="Exit with status 1 if any expected or forbidden substring check fails")
    a=p.parse_args()
    summary=run_benchmark(a.model_id,a.cases,a.output,a.max_new_tokens,a.device)
    print(json.dumps(summary,indent=2))
    if a.fail_on_regression and not summary["quality_gate"]["passed"]:
        sys.exit(1)
if __name__=="__main__":main()
