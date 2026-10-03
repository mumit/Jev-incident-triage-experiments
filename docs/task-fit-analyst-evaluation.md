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

Preparation commit: `3f3c8b8`. All 24 held-out calls completed without failures. Source, boundary, request and response fingerprints verify, and recomputation reproduces the [evaluation summary](../checkpoints/task-fit-evaluation-2026-10-03.json) and [advisory assessment](../checkpoints/task-fit-analyst-assessment-2026-10-03.json). The workbench now exposes the verified evaluation. A fresh clone without the raw runs keeps its cases unavailable.

The next operational evidence needs appropriately handled real reports and specialist-reviewed references. Analysts would inspect the source, recommendation and policy, record agreement or correction, and measure review effort. Further model changes need new development cases; this evaluation cannot serve as a tuning set or be rerun to replace an inconvenient result. Idle-handler semantics and other model providers remain outside this stage.


## Held-out results

| Measure | Development, Structured | Calibration, Structured | Held-out evaluation, Structured |
|---|---|---|---|
| Correct report readings | 24/24 | 23/24 | 21/24 |
| Correct packet decisions | 24/24 | 23/24 | 22/24 |
| Qualifying readings at 0.60 | Not used for boundary selection | 16/24 | 17/24 |
| Domain suggestions at 0.60 | Not used for boundary selection | 9/24 | 9/24 |
| Wrong domain suggestions at 0.60 | Not used for boundary selection | 0/9 | 1/9 |

Evaluation meets the two coverage floors and completes every call, but fails both the zero-wrong-domain and zero-wrong-qualifying-reading criteria. All eight reference faults receive fault readings; none becomes a qualifying normal reading. The nine domain suggestions include eight correct suggestions and one incorrect core suggestion. All 24 reports still require analyst review.

Three report errors explain the result:

| Case | Report evidence | Draft reference → actual reading | Consequence |
|---|---|---|---|
| `NTF-9df8eaf75258-a` | After repair, the handler admits valid requests as specified; end-to-end completion is not measured. | normal → unknown, probability 0.67 | Suggestion withheld. Correct NOC routing hides the reading error. |
| `NTF-ce9267c9a469-a` | The caller times out waiting for completion; intake receipts verify acceptance of valid requests. | normal → fault, probability 0.84 | Wrong core-team suggestion passes the frozen 0.60 threshold. |
| `NTF-ce9267c9a469-b` | The caller times out; receipts were not captured, so admission is unconfirmed. | unknown → fault, probability 0.57 | The advisory boundary withholds the suggestion, although raw policy alone would recommend core. |

The paired timeout reports reveal a recurring scope problem. Jev treats failed end-to-end completion as a handler fault even when acceptance is verified or unconfirmed. The report's focal function is supplied, so these failures cannot be attributed simply to omitted scope metadata. Unknown and normal errors both matter: a confident false fault can cause an unnecessary team assignment, while a wrong unknown can hide correct evidence and increase investigation effort.

Median client latency is 141 ms and the 95th percentile is 195 ms. Provider-reported usage is 11,735 input and 912 output tokens. Multiclass Brier score is 0.1511 and log loss is 0.2396. These are small synthetic measurements, not operational probability calibration or billed cost.

## What this changes

I would keep Jev as an analyst-assistance candidate, with its evidence visible and every suggestion reviewed. This evaluation does not support claiming that a confidence-qualified suggestion is reliable, and it does not establish a fair ranking against an adequately trained ML reader.

The next input experiment should test explicit function definitions on new development families. For example, the request could explain that `request_intake` measures admission of valid requests and excludes downstream completion, while preserving the complete original report. That definition describes the task; it must not insert a normal/fault answer or remove conflicting evidence. The existing Focused arm added general measured-function wording on an earlier pack; it did not establish that explicit semantic definitions fix these held-out failures.

Raising the threshold after seeing the 0.84 error would reuse evaluation evidence to select a new boundary. The 0.60 result remains recorded. A revised reader or boundary needs new development/calibration cases and a new held-out set.

Before an operational study, specialists need to review the reference meanings and supply a range of appropriately handled real reports. The [analyst review plan](analyst-review-plan.md) prepares that work. No real reports or specialist judgments are present in this repository; that evidence is the current external dependency.
