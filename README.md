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
python benchmark.py --model-id distilgpt2 --cases examples/cases.jsonl --minimum-failing-severity high

Exports JSON, CSV, a provenance manifest, a static self-contained HTML report, per-case latency, and local input/output token counts (API runs include latency; provider token usage is not currently parsed). Add --fail-on-regression in scripts or CI to return a non-zero exit code when expected substrings are missing or forbidden substrings are found. The optional --minimum-failing-severity flag accepts low, normal, high, or critical and only blocks at that severity or above; lower-severity findings remain visible in the report. JSONL cases require a prompt and may include a unique ID, category, severity, expected substring, and forbidden substrings. Outputs include per-case latency; local inference also records input/output token counts. A self-contained HTML report summarizes category scorecards and results. Invalid JSON, duplicate IDs, and malformed case fields are rejected with line-aware errors.

## Evaluate an OpenAI-compatible API

The API-only runner needs no PyTorch, Transformers, or GPU. Set your provider key in an environment variable (never commit it), then run:

    export OPENAI_API_KEY="..."
    python api_benchmark.py --base-url https://api.example.com/v1 --model-id your-model --cases examples/cases.jsonl --minimum-failing-severity high

On Windows PowerShell, use $env:OPENAI_API_KEY = "...". Replace the example URL and model with values from your provider. The adapter expects a POST /chat/completions response. API keys are not written to result files. Check your provider's data-retention terms before sending prompts.

## Compare two saved model runs

    python compare_models.py --results outputs/baseline/results.json outputs/candidate/results.json --labels baseline candidate --fail-on-regression

The comparison utility aligns results by case ID, identifies newly failing expected checks, missing candidate cases and new forbidden-phrase hits, and exports JSON/CSV plus a static HTML report. The first file is the baseline and the second is the candidate. With --fail-on-regression, the process exits non-zero when a regression is found, making it suitable for a CI gate. Run each model with benchmark.py first. This is a textual regression comparison, not a semantic quality ranking.

## GitHub Actions integration

See [examples/github-actions.yml](examples/github-actions.yml) for a template that runs the API evaluator on pull requests and uploads JSON/CSV/HTML artifacts. Copy it into the application repository, store the API key as the `LLM_API_KEY` secret, and configure `LLM_API_BASE_URL` and `LLM_MODEL_ID` as repository variables. The example assumes that repository contains `examples/cases.jsonl`.

## Case format

See [CASE_FORMAT.md](CASE_FORMAT.md) for the JSONL schema, category/severity conventions, and quality-gate behavior.

## What the scores mean

Substring checks are simple regression signals, not semantic evaluation. A passing case does not prove correctness, and a forbidden phrase may occur in a negated or quoted context. Review completions and maintain a representative, versioned test set.

## Deployment and security

See [DEPLOYMENT.md](DEPLOYMENT.md) for local setup and regression-gated runs, and [SECURITY.md](SECURITY.md) for deployment cautions and vulnerability reporting. The current dashboard is local-only; it is not yet a secured multi-user SaaS.

## License

MIT.
