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
python benchmark.py --model-id distilgpt2 --cases examples/cases.jsonl --fail-on-regression

Exports JSON, CSV, a provenance manifest, and a quality-gate summary. Add --fail-on-regression in scripts or CI to return a non-zero exit code when expected substrings are missing or forbidden substrings are found. JSONL cases require a prompt and may include a unique ID, expected substring, and forbidden substrings. Invalid JSON, duplicate IDs, and malformed case fields are rejected with line-aware errors.

## Compare two saved model runs

    python compare_models.py --results outputs/baseline/results.json outputs/candidate/results.json --labels baseline candidate --fail-on-regression

The comparison utility aligns results by case ID, identifies newly failing expected checks and new forbidden-phrase hits, and exports JSON/CSV. The first file is the baseline and the second is the candidate. With --fail-on-regression, the process exits non-zero when a regression is found, making it suitable for a CI gate. Run each model with benchmark.py first. This is a textual regression comparison, not a semantic quality ranking.

## What the scores mean

Substring checks are simple regression signals, not semantic evaluation. A passing case does not prove correctness, and a forbidden phrase may occur in a negated or quoted context. Review completions and maintain a representative, versioned test set.

## Deployment and security

See [DEPLOYMENT.md](DEPLOYMENT.md) for local setup and regression-gated runs, and [SECURITY.md](SECURITY.md) for deployment cautions and vulnerability reporting. The current dashboard is local-only; it is not yet a secured multi-user SaaS.

## License

MIT.
