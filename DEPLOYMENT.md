# Local Deployment Guide

Behavior Bench is currently intended for a single developer or evaluator running locally. Do not deploy the dashboard as a public multi-user service: authentication, tenant isolation, and production access controls are not implemented.

## 1. Install

Python 3.11 is the CI-tested runtime.

```bash
git clone https://github.com/eliem08/behavior-bench.git
cd behavior-bench
python -m venv .venv
```

Activate the environment:

- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.\.venv\Scripts\Activate.ps1`

Then install and start:

```bash
python -m pip install -r requirements.txt
streamlit run dashboard.py
```

Open the local URL printed by Streamlit. The first model run may download model weights from Hugging Face; subsequent runs may use the local cache.

## 2. Run a quality-gated benchmark

```bash
python benchmark.py --model-id distilgpt2 --cases examples/cases.jsonl --fail-on-regression
```

The command writes JSON and CSV outputs under `outputs/benchmark/`. A non-zero exit status means at least one expected-substring check failed or a forbidden substring was found. These checks are intentionally simple and require human review.

## 3. Evaluate a hosted OpenAI-compatible API

The API-only runner uses Python's standard library and does not require PyTorch, Transformers, or a GPU. Set a provider API key in your shell, then run:

    export OPENAI_API_KEY="..."
    python api_benchmark.py --base-url https://api.example.com/v1 --model-id your-model --cases examples/cases.jsonl --fail-on-regression

Replace the example URL/model with your provider's values. The adapter uses the standard chat-completions shape. Do not put API keys in command-line arguments, source files, notebooks, or result artifacts. Review the provider's data processing and retention terms before sending sensitive prompts.

## 4. Compare against a baseline

Run the baseline model/test set first and preserve its `results.json`. Run the candidate using a separate output directory, then compare:

```bash
python compare_models.py --results outputs/baseline/results.json outputs/candidate/results.json --labels baseline candidate --fail-on-regression
```

The first file is treated as the baseline and the second as the candidate. The gate flags a previously passing expected check that now fails, or newly observed forbidden-substring hits.

## 5. GitHub Actions integration

Copy [examples/github-actions.yml](examples/github-actions.yml) into the target application's `.github/workflows/behavior-bench.yml`. Configure the `LLM_API_KEY` repository secret and the `LLM_API_BASE_URL` and `LLM_MODEL_ID` repository variables. The target repository must store its cases at `examples/cases.jsonl`. The workflow uploads JSON, CSV, and HTML artifacts and fails when configured substring checks fail.

## 6. Hardware

- CPU: supported for small models, but inference can be slow.
- CUDA GPU: use `--device cuda` when the installed PyTorch build and driver support it.
- Apple Silicon: use `--device mps` when supported.
- Google Colab: use the linked notebook to select an available accelerator.

## 7. Production-readiness limitations

Before serving teams or customer data, add authentication, per-user authorization, tenant isolation, request and file-size limits, secure secret management, durable database-backed run history, audit logs, retention/deletion controls, dependency pinning, and security review. Do not claim these features are present until implemented and tested.
