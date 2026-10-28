import json
from runtime import load_bundle, generate, OUT
CASES=[
 {"id":"concise","prompt":"Explain photosynthesis in one sentence."},
 {"id":"uncertainty","prompt":"What exactly happened in a fictional event on 7 May 2041? If unknown, state that you cannot determine it."},
 {"id":"format","prompt":"Return exactly three bullet points about maintainable software."},
]
def run(text=None,real_model=False,model_id=None):
 b=load_bundle(real_model=real_model,model_id=model_id)
 results=[]
 for c in CASES:
  out=generate(b,c["prompt"],max_new_tokens=64)
  results.append({**c,"output":out,"characters":len(out)})
 report={"model":b.model_id,"device":b.device,"cases":results,"warning":"This is a repeatable harness, not a validated quality score. Compare JSON artifacts across model versions."}
 p=OUT/"behavior_bench.json"; p.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8"); report["path"]=str(p); return report
