"""Run reproducible prompt regression cases against a causal language model.

Input JSONL rows accept: id, prompt, expected_substring (optional), forbidden_substrings (optional list).
This is a lightweight regression harness, not a comprehensive quality or safety evaluation.
"""
from __future__ import annotations
import argparse, json, hashlib, csv
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def load_cases(path):
    cases = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    for i, c in enumerate(cases):
        if not isinstance(c.get("prompt"), str) or not c["prompt"].strip():
            raise ValueError(f"Case {i+1} needs a non-empty prompt")
        c.setdefault("id", f"case-{i+1:03d}")
        c.setdefault("forbidden_substrings", [])
    return cases

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
    (out/"results.json").write_text(json.dumps({"model_id":model_id,"device":device,"cases":rows},indent=2,ensure_ascii=False),encoding="utf-8")
    with (out/"results.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["id","prompt","completion","expected_substring","expected_pass","forbidden_hits","completion_sha256"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:
            r2=dict(r);r2["forbidden_hits"]="; ".join(r["forbidden_hits"]);w.writerow(r2)
    checked=[r for r in rows if r["expected_pass"] is not None]
    summary={"model_id":model_id,"device":device,"total":len(rows),"expected_checks":len(checked),"expected_pass_rate":sum(bool(r["expected_pass"]) for r in checked)/len(checked) if checked else None,"cases_with_forbidden_hits":sum(bool(r["forbidden_hits"]) for r in rows),"output":str(out)}
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--model-id",default="distilgpt2");p.add_argument("--cases",default="examples/cases.jsonl");p.add_argument("--output",default="outputs/benchmark");p.add_argument("--max-new-tokens",type=int,default=96);p.add_argument("--device",choices=["auto","cpu","cuda","mps"],default="auto")
    a=p.parse_args();print(json.dumps(run_benchmark(a.model_id,a.cases,a.output,a.max_new_tokens,a.device),indent=2))
if __name__=="__main__":main()
