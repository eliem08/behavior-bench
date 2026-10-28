# Behavior Bench — Product Roadmap

## Product outcome

A versioned regression-testing platform for LLM applications: define cases, run them against models or API adapters, compare releases, and stop regressions before deployment.

## Users and problem

- AI product engineers shipping prompts or model changes.
- Evaluation teams maintaining repeatable test suites.
- Small teams that need CI checks without buying a full enterprise evaluation platform.

## Current foundation

- JSONL case format, deterministic generation, substring checks, JSON/CSV outputs.
- Interactive dashboard, Colab notebook, tests and CI.

## Roadmap

### Phase 1 — Useful regression suite
- [x] Add strict JSONL schema validation, unique case IDs, and an opt-in CLI exit code for failed checks.
- [ ] Add semantic rubric hooks as optional pluggable evaluators; label model-graded scores separately.
- [ ] Track latency, token counts, exceptions, and reproducibility metadata.
- [x] Compare saved run artifacts by case ID and highlight changed outputs / expected-check changes.\n- [ ] Add a richer HTML diff report and category-level summaries.
- [ ] Add fixtures for prompt injection, refusal, factuality, structured output, and tool-use behavior.

### Phase 2 — Team-ready testing
- [x] Add a hosted OpenAI-compatible API adapter with API keys read from environment variables.
- [x] Add CLI gates for expected/forbidden phrase checks and baseline-vs-candidate regressions; add a CI example and richer thresholds next.
- [ ] Dataset versioning, tags, owner, severity, and review workflow.
- [ ] Bootstrap confidence intervals and per-category scorecards.
- [ ] HTML report export and run history.

### Phase 3 — Final product
A self-hosted or hosted LLM quality gate: suites live in Git, CI runs evaluation matrices, dashboards compare model/prompt releases, and teams receive actionable regression reports before rollout.

## Success criteria

- A new team can add its first case in under five minutes.
- Results are diffable and include model/config metadata.
- CI failure conditions are explicit and tested.
- Heuristic checks are never presented as comprehensive quality scores.
