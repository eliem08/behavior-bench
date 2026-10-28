# Behavior Bench

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eliem08/behavior-bench/blob/main/colab.ipynb)

A lightweight prompt-regression harness for comparing a model against explicit expected and forbidden text checks.

## Run a benchmark

    pip install -r requirements.txt
    python benchmark.py --model-id distilgpt2 --cases examples/cases.jsonl

The runner uses deterministic greedy decoding and exports outputs/benchmark/results.json, results.csv, and summary.json. Each JSONL case needs a prompt; optionally provide id, expected_substring, and forbidden_substrings.

    python benchmark.py --model-id distilgpt2 --device cuda --max-new-tokens 80

The device auto-option selects CUDA, Apple MPS, or CPU. Open colab.ipynb in Colab for a notebook workflow.

## What the scores mean

Substring checks are simple regression signals, not semantic evaluation. A passing case does not prove correctness, and a forbidden phrase may occur in a negated or quoted context. Review completions and maintain a representative, versioned test set.

## Quickstart

    python main.py

The original demo uses random weights to check the pipeline; use a pretrained model for real prompt evaluation.

## License

MIT.
