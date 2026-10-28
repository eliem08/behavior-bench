"""Streamlit dashboard for Behavior Bench. Run: streamlit run dashboard.py"""
import json
import os
from pathlib import Path
import streamlit as st
import pandas as pd
from benchmark import run_benchmark
from api_benchmark import run_api_benchmark

st.set_page_config(page_title="Behavior Bench", layout="wide")
st.title("Behavior Bench")
st.caption("Prompt regression testing with explicit checks; substring metrics require human review.")
provider = st.selectbox("Provider", ["Local Hugging Face", "OpenAI-compatible API"])
model = st.text_input("Model ID", "distilgpt2" if provider == "Local Hugging Face" else "")
cases = st.text_input("JSONL case file", "examples/cases.jsonl")
tokens = st.slider("Maximum new tokens", 16, 256, 96, step=16)
if provider == "Local Hugging Face":
    device = st.selectbox("Device", ["auto", "cuda", "mps", "cpu"])
else:
    base_url = st.text_input("API base URL", placeholder="https://api.example.com/v1")
    key_env = st.text_input("API key environment variable", "OPENAI_API_KEY")
    st.caption("The key is read from the server environment; it is never saved in the dashboard or results.")

if st.button("Run benchmark", type="primary"):
    try:
        with st.spinner("Running test cases…"):
            if provider == "Local Hugging Face":
                summary = run_benchmark(model, cases, max_new_tokens=tokens, device=device)
            else:
                api_key = os.environ.get(key_env)
                if not api_key:
                    raise ValueError(f"Set {key_env} in the environment where Streamlit is running.")
                if not base_url.strip() or not model.strip():
                    raise ValueError("Enter the API base URL and model ID.")
                summary = run_api_benchmark(model, cases, base_url, api_key, max_new_tokens=tokens)
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
        payload = json.loads((Path(summary["output"]) / "results.json").read_text(encoding="utf-8"))
        st.dataframe(pd.json_normalize(payload["cases"]), use_container_width=True)
        st.download_button("Download JSON results", json.dumps(payload, indent=2), file_name="benchmark-results.json")
    except Exception as exc:
        st.error(f"Benchmark failed: {exc}")
        st.info("Check the case-file path, model access, available memory, and selected device.")
