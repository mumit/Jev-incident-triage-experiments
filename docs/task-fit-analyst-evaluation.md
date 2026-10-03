# Analyst-facing Jev recommendations

## Purpose

The user selected analyst-facing recommendations on October 3, 2026. I will evaluate whether the frozen Structured reader can supply useful suggestions while an analyst retains every initial-team assignment. The study executes no ticket assignment or network change.

The [task-fit experiment](task-fit-experiment.md) records development and calibration. This stage uses its 24 procedurally sealed synthetic evaluation reports in 12 families. The same author wrote all splits, and references remain unreviewed drafts. Held-out performance here cannot establish network realism or operational reliability.

## Frozen recommendation boundary

The reader, `jev-1.13.0`, complete report text, focal-function metadata, question and declaration-consistency policy stay unchanged. The separate [analyst boundary](../checkpoints/task-fit-analyst-boundary-2026-10-03.json) adds a display rule after interpretation:

- A fault or normal reading qualifies at a returned-reading probability of at least **0.60**.
- A domain suggestion also requires the frozen policy to identify a domain with sufficient evidence. Qualifying normal readings can still retain NOC while service impact remains unresolved.
- Unknown readings, low-probability answers and failed or missing responses request clarification. The actual reply and software policy remain inspectable.
- **Every report requires analyst review**, including qualifying readings and domain suggestions. A suggestion never becomes an automatic assignment.

Calibration selected 0.60 by maximizing qualifying reading coverage with zero observed reading errors and qualifying fault misses, breaking ties at the lowest threshold. At that threshold, 16/24 readings qualify and 9/24 reports yield domain suggestions, with zero observed errors. Evaluation contributes nothing to threshold selection. The provider's separate confidence value does not control the boundary.

## Research criteria

I set these provisional criteria before evaluation. They are synthetic research gates, not operating limits approved by the user or specialists.

| Measure | Criterion | Meaning for 24 reports |
|---|---|---|
| Wrong domain suggestions | Zero observed | No displayed domain conflicts with its draft reference. |
| Wrong qualifying readings | Zero observed | Neither a fault nor a normal suggestion misstates its draft report meaning. |
| Qualifying fault misses | Zero observed | No qualifying normal reading hides a reference fault. Unknown and withheld faults remain visible in the full report metrics. |
| Qualifying reading coverage | At least 50% | At least 12 reports provide a reading suggestion. |
| Domain suggestion coverage | At least 25% | At least six reports provide a domain suggestion. |
| Failed or missing responses | Zero | All planned calls must complete successfully. Failures still count in the denominators. |

The coverage floors ensure that the study exercises more than a few suggestions. They do not estimate useful coverage or acceptable errors in a real NOC. Zero observed errors on this small paired sample cannot demonstrate a safe error rate. Analysts may also disagree with the draft references.

## Execution and evidence

Preparation freezes the candidate, calibration summary, advisory threshold, criteria and new evaluation source fingerprints before any evaluation call. The preregistered output is `runs/task-fit/evaluation-2026-10-03-v1/`. Its directory cannot be reused or replaced.

The separate evaluation wrapper preserves historical inference code. It sends exactly 24 requests serially, without warmup or retries, and records the full request plan before the first call. Access, rate-limit, network and version errors stop execution; three consecutive malformed responses also stop it. Failure-inclusive scoring retains all 24 planned reports.

Full report and packet scores remain separate from the advisory assessment. The assessment counts qualifying readings, domain suggestions, incorrect suggestions, withheld readings and all required analyst reviews. It measures neither analyst agreement nor time saved. The original development, repeat and calibration evidence remains unchanged.

```bash
uv run --locked python -m scripts.run_task_fit_advisory preflight
uv run --locked python -m scripts.run_task_fit_advisory evaluate
uv run --locked python -m scripts.run_task_fit_advisory assess --output runs/task-fit/evaluation-2026-10-03-v1
```

Boundary creation and preflight are already recorded. Evaluation uses the server-side key and incurs provider charges. Inspection and assessment make no model calls. The historical public bundle excludes this study's raw runs.

## Status and next step

The advisory boundary is frozen; evaluation has not run. Once its evidence verifies, the workbench can expose the completed evaluation alongside development and calibration. A fresh clone without raw evidence must show its absence explicitly.

The next operational evidence needs appropriately handled real reports and specialist-reviewed references. Analysts would inspect the source, recommendation and policy, record agreement or correction, and measure review effort. Further model changes need new development cases; this evaluation cannot serve as a tuning set or be rerun to replace an inconvenient result. Idle-handler semantics and other model providers remain outside this stage.
