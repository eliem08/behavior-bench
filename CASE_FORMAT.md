# Evaluation Case Format

Each non-empty line in a JSONL file is one test case. UTF-8 is recommended. IDs must be unique within a suite.

## Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | No | Stable case identifier; generated when omitted |
| `prompt` | Yes | User message sent to the model |
| `category` | No | Scorecard grouping; defaults to `uncategorized` |
| `severity` | No | `low`, `normal`, `high`, or `critical`; defaults to `normal` |
| `expected_substring` | No | Text that must occur in the completion for this simple check to pass |
| `forbidden_substrings` | No | List of text strings that must not occur in the completion |
| `expected_json` | No | Expected JSON object subset; nested values are checked recursively, while extra keys are allowed |
| `required_json_keys` | No | List of required JSON key paths; use dots for nested objects, e.g. `data.count` |

Example:

```jsonl
{"id":"factuality-001","category":"factuality","severity":"high","prompt":"If you cannot verify a claim, what should you say?","expected_substring":"cannot verify","forbidden_substrings":["guaranteed accurate"]}
{"id":"format-001","category":"formatting","severity":"low","prompt":"List three steps.","expected_substring":"1","forbidden_substrings":[]}
```

## Gate behavior

- Without a severity threshold, any failed expected-substring check, forbidden-substring hit, or configured structured JSON check fails the quality gate.
- Structured checks run only when `expected_json` or `required_json_keys` is configured. Completions must be valid JSON; `expected_json` checks the configured object subset and `required_json_keys` checks required dotted paths.
- `--minimum-failing-severity high` fails only on `high` and `critical` findings. Lower-severity findings remain in the report.
- `--minimum-failing-severity critical` fails only on critical findings.
- `--fail-on-regression` returns a non-zero process exit code when the selected gate fails.
- Severity is metadata supplied by the suite author; it is not inferred by the model or evaluator.

## Important limitations

Substring matching is not semantic evaluation. It can miss meaning-preserving paraphrases and can flag text appearing in quotes or negations. Do not use a passing gate as proof of safety, correctness, legal compliance, or factuality. Add representative cases, review completions, and use a separate semantic/human evaluation process for high-stakes uses.

Treat prompts and completions as potentially sensitive. Do not commit customer secrets, personal data, or confidential business content to a public repository.
