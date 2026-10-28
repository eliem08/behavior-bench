# Model-Graded Rubric Evaluation

Behavior Bench can optionally score saved model outputs using a second OpenAI-compatible model as a judge.

## Usage

First run a benchmark and preserve its `results.json`. Then set a judge-provider key in your shell and run:

```bash
export OPENAI_API_KEY="..."
python rubric_eval.py \
  --results outputs/api-benchmark/results.json \
  --base-url https://api.example.com/v1 \
  --judge-model-id your-judge-model \
  --minimum-average-score 3.5
```

PowerShell: set `$env:OPENAI_API_KEY` before running the command. Replace the example URL and judge model with values from your provider.

The evaluator returns 1–5 scores for correctness, relevance, instruction-following, and safety, plus a rationale and confidence label. It writes `rubric.json` and `rubric.csv` to the output directory. The judge model is separate from the target model identifier, but the same endpoint/key is used unless you adapt the runner.

## Optional threshold

Add `--fail-on-low-score` to return a non-zero exit code when any case's mean score is below `--minimum-average-score`. Without the flag, the threshold is reported but does not fail the process.

## Limitations

- Scores are model-graded heuristics, not ground truth, validated benchmarks, or safety certification.
- Judge models can be biased, inconsistent, or vulnerable to prompt injection in candidate outputs.
- Review rationales and disagreements manually before using scores for consequential release decisions.
- The rubric output contains prompts and model completions; protect artifacts as potentially sensitive.
- Review provider retention and data-processing terms before sending private data.
