"""Streamlit dashboard for Behavior Bench. Run: streamlit run dashboard.py"""
import json
from pathlib import Path
import streamlit as st
import pandas as pd
from benchmark import run_benchmark

st.set_page_config(page_title="Behavior Bench", layout="wide")
st.title("Behavior Bench")
st.caption("Prompt regression testing with explicit checks; substring metrics require human review.")
model = st.text_input("Model ID", "distilgpt2")
cases = st.text_input("JSONL case file", "examples/cases.jsonl")
device = st.selectbox("Device", ["auto", "cuda", "mps", "cpu"])
tokens = st.slider("Maximum new tokens", 16, 256, 96, step=16)

if st.button("Run benchmark", type="primary"):
    try:
        with st.spinner("Running test cases…"):
            summary = run_benchmark(model, cases, max_new_tokens=tokens, device=device)
        st.metric("Cases", summary["total"])
        rate = summary["expected_pass_rate"]
        st.metric("Expected substring pass rate", "n/a" if rate is None else f"{rate:.1%}")
        st.metric("Cases with forbidden phrase", summary["cases_with_forbidden_hits"])
        gate = summary["quality_gate"]
        if gate["passed"]:
            st.success("Quality gate passed")
        else:
            st.error(f"Quality gate found {gate['failure_count']} regression signal(s)")
            st.dataframe(pd.DataFrame(gate["failures"]), use_container_width=True)
        st.caption("Substring checks are transparent regression signals, not semantic quality or safety certification.")
        payload = json.loads(Path("outputs/benchmark/results.json").read_text(encoding="utf-8"))
        st.dataframe(pd.json_normalize(payload["cases"]), use_container_width=True)
        st.download_button("Download JSON results", json.dumps(payload, indent=2), file_name="benchmark-results.json")
    except Exception as exc:
        st.error(f"Benchmark failed: {exc}")
        st.info("Check the case-file path, model access, available memory, and selected device.")
