"""Streamlit dashboard for Behavior Bench. Run: streamlit run dashboard.py"""
import streamlit as st
import pandas as pd
from benchmark import run_benchmark
st.set_page_config(page_title="Behavior Bench",layout="wide")
st.title("Behavior Bench")
st.caption("Prompt regression testing with explicit checks; substring metrics require human review.")
model=st.text_input("Model ID","distilgpt2")
cases=st.text_input("JSONL case file","examples/cases.jsonl")
device=st.selectbox("Device",["auto","cuda","mps","cpu"])
tokens=st.slider("Maximum new tokens",16,256,96,step=16)
if st.button("Run benchmark",type="primary"):
    with st.spinner("Running test cases…"):
        summary=run_benchmark(model,cases,max_new_tokens=tokens,device=device)
    st.metric("Cases",summary["total"])
    st.metric("Expected substring pass rate", "n/a" if summary["expected_pass_rate"] is None else f"{summary['expected_pass_rate']:.1%}")
    st.metric("Cases with forbidden phrase",summary["cases_with_forbidden_hits"])
    st.json(summary)
    df=pd.read_json("outputs/benchmark/results.json")
    st.dataframe(pd.json_normalize(df["cases"]),use_container_width=True)
