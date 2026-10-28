# Behavior Bench

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eliem08/behavior-bench/blob/main/colab.ipynb)

A lightweight prompt-regression harness for comparing a model against explicit expected and forbidden text checks.

## Interactive dashboard

    pip install -r requirements.txt
    streamlit run dashboard.py

Run the sample case suite, inspect completions, and review basic pass-rate and forbidden-phrase metrics.

## Run a benchmark

    python benchmark.py --model-id distilgpt2 --cases examples/cases.jsonl
    python benchmark.py --model-id distilgpt2 --device cuda --max-new-tokens 80

Exports JSON, CSV, and a summary. JSONL cases require a prompt and may include an ID, expected substring, and forbidden substrings.

## What the scores mean

Substring checks are simple regression signals, not semantic evaluation. A passing case does not prove correctness, and a forbidden phrase may occur in a negated or quoted context. Review completions and maintain a representative, versioned test set.

## License

MIT.
