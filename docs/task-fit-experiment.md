# Jev report interpretation: task-fit experiment

## Purpose

I am testing which changes improve Jev's interpretation of incident reports for Northstar Telecom. The experiment separates input format, question wording and training examples. Software applies the frozen declaration-consistency policy after each reading.

This is a synthetic study with draft references. It cannot establish operational accuracy or replace specialist review. The [research assessment](jev-task-fit.md) explains the motivation. The idle-handler definition remains deferred; this pack contains no scored idle outcomes.

## Data and controls

| Split | Reports | Families / pairs | Use |
|---|---|---|---|
| Training | 16 | 8 | Six preselected examples: two fault, two normal and two unknown. No Jev training calls. |
| Development | 24 | 12 | Compare four arms and select a reader. |
| Calibration | 24 | 12 | Describe the frozen reader's probabilities and review coverage. |
| Evaluation | 24 | 12 | Remains sealed until the operating-boundary protocol is recorded. |

Each packet has one report. Each family has two related reports that change only the report text. Families and full report texts are disjoint across splits; common vocabulary, concepts and the author's style remain shared. Evaluation is procedurally sealed, not independently authored or a sample of real incidents.

The cases cover RAN, transport, power and core. They include negation, earlier alarms, a failed auxiliary function, missing traces, expected rejection of malformed requests, counter resets, successful intermediate operations and instructions embedded in logs. Currentness, service linkage and instrument declarations are supplied synthetic facts and held fixed within pairs. This study isolates interpretation; it does not test metadata trust or raw KPI anomaly detection.

Report annotations describe the outcome of the measured function. Packet references describe the four downstream decisions. Both are written before inference and stay in separate files. Reference-fed policy checks diagnose implementation consistency; they do not constitute model performance.

## What changes in Jev's request

All arms use pinned `jev-1.13.0` and ask one Choice question: `fault`, `normal` or `unknown`. The domain comes from structured instrument metadata in software and is not a model output.

| Arm | State | Question | Matched comparison |
|---|---|---|---|
| Prose | Focal function and full report in a plain text layout. | Frozen original report-reading instructions and criteria. | Control. |
| Structured | The same focal function and full report in JSON. | Identical to Prose. | Format only. |
| Focused | Identical JSON to Structured. | Adds the existing measured-function clarification plus explicit treatment of report text as evidence. Criteria stay fixed. | Related wording clarifications together; individual sentences are not isolated. |
| Examples | Focused JSON plus six preselected labeled training reports. | Identical to Focused. | Training examples only. |

For example, both initial arms carry the same facts:

```text
Focal function: request_intake
Report text:
Instrument domain: core. The intake handler correctly accepted each valid request. A downstream worker refused completion; intake itself operated correctly.
```

```json
{
  "focal_function": "request_intake",
  "report_text": "Instrument domain: core. The intake handler correctly accepted each valid request. A downstream worker refused completion; intake itself operated correctly."
}
```

The Focused arm asks about the supplied function, so intake success remains normal even when downstream completion fails. No input transformation inserts a predicted reading, deletes a conflicting clause or supplies a packet answer. Only the Examples arm receives reference readings, and those belong exclusively to preselected training reports.

Frozen report rules and the two earlier report ML readers provide bridge controls. They receive report text only, without focal-function metadata. Their comparison with Jev therefore differs in available information and is not a matched model ranking. They keep their original training data and settings.

## Execution and selection

Development requires 96 primary Jev calls. A preregistered repeat checks six reports three times across all four arms, adding 72 calls. Primary and repeat scores remain separate. Rotated arm order limits ordering effects; calls are serial, with no warmup or automatic retry. Access, rate-limit, network and checkpoint errors stop the run, and failures remain in denominators.

Reader selection uses development evidence only: most correct readings, then fewer missed fault readings, then fewer label flips on the six repeated reports, then the simpler arm. Calibration cannot change the selected reader. The candidate checkpoint records its model, question, examples, source and data fingerprints.

Calibration evaluates that frozen reader in 24 calls. Confidence curves use the probability of the returned reading, not the provider's separate confidence field. Unknown, failed and missing responses require review regardless of confidence. No sweep point becomes an operational threshold automatically.

## Results to inspect

Primary measures include report accuracy, fault/normal/unknown confusion, fully correct pairs, downstream packet matches and wrong readings hidden by those matches. Misread faults remain visible, including unavailable responses. Repeatability records label changes separately from correctness.

Multiclass Brier score, log loss and reliability bins describe probability quality on successfully scored reports. Failed calls remain in coverage and accuracy totals, but have no invented probability. Review curves show coverage, reading errors, packet errors and accepted fault misses at explicit thresholds. Twenty-four calibration reports are too few to establish operational reliability. A zero observed error count must not imply zero risk, and paired reports reduce independence further.

Actual requests, raw replies, policy traces and local fitted explanations stay in immutable ignored run directories. Tracked checkpoints summarize measured evidence; a fresh clone without the runs must show missing predictions explicitly.

## Reproduce

```bash
uv run --locked python -m scripts.run_task_fit validate
uv run --locked python -m scripts.run_task_fit preflight
uv run --locked python -m scripts.run_task_fit local --output runs/task-fit/local-v1
uv run --locked python -m scripts.run_task_fit hosted --output runs/task-fit/development-v1
uv run --locked python -m scripts.run_task_fit hosted --repeat --output runs/task-fit/repeat-v1
uv run --locked python -m scripts.run_task_fit freeze --development runs/task-fit/development-v1 --repetition runs/task-fit/repeat-v1 --output checkpoints/task-fit-candidate.json
uv run --locked python -m scripts.run_task_fit hosted --split calibration --arm SELECTED_ARM --freeze checkpoints/task-fit-candidate.json --output runs/task-fit/calibration-v1
uv run --locked python -m scripts.run_task_fit verify --output runs/task-fit/development-v1
```

Replace `SELECTED_ARM` with the recorded candidate. Hosted execution uses the ignored local configuration and incurs provider charges. Existing output directories cannot be reused. This protocol introduces no other model provider and executes no network actions.

## Current state

Preparation source: `b72a533`. All 96 primary calls and 72 repeated calls completed without failures. The 72 local predictions are classifier/rule outputs, not hosted calls. [Primary results](../checkpoints/task-fit-development-2026-10-03.json), [repeated diagnostic](../checkpoints/task-fit-repeat-2026-10-03.json), [local controls](../checkpoints/task-fit-local-2026-10-03.json).

| Jev arm | Correct readings / 24 | Correct reading pairs / 12 | Packet matches / 24 | Wrong readings hidden by packet matches |
|---|---|---|---|---|
| Prose | 23 | 11 | 24 | 1 |
| Structured | 24 | 12 | 24 | 0 |
| Focused | 24 | 12 | 24 | 0 |
| Examples | 24 | 12 | 24 | 0 |

The Prose arm reads the current verified timing recovery as `unknown`: “Earlier notes reported loss of timing. The current alignment test verifies synchronization to the required reference.” Structured input returns `normal`. Both readings retain NOC under the frozen degraded-service policy, so packet accuracy hides this report error. The format comparison fixes one reading and loses none. Additional wording and training examples add no correct readings on this pack.

All four arms match the six preselected reports in every repeat, without label flips. The timing-recovery failure was not among those six; repetition does not establish that its format difference will persist.

Reported primary input tokens are 11,605 for Prose, 11,727 for Structured, 14,655 for Focused and 20,583 for Examples. Additional wording and examples increase token usage without an observed accuracy gain here. Median client request latency is approximately 133–140 ms across arms. These figures describe this machine and these successful calls; usage is not reconciled billing.

Frozen rules match 7/24 readings and 15/24 packets, with eight hidden reading errors. Each frozen ML reader matches 6/24 readings and 16/24 packets, hiding ten reading errors. These text-only controls have different context and limited training coverage; their results do not establish general model superiority.

The [candidate freeze](../checkpoints/task-fit-candidate-2026-10-03.json) selects **Structured** using the predeclared development rule. Its question and input construction stay unchanged for calibration. No operating threshold is selected, and final evaluation remains sealed. Operational use also requires specialist-reviewed examples and an explicit choice of acceptable errors and useful coverage.
