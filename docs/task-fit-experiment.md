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
| Evaluation | 24 | 12 | Completed once under the frozen analyst-facing boundary; now inspectable. |

Each packet has one report. Each family has two related reports that change only the report text. Families and full report texts are disjoint across splits; common vocabulary, concepts and the author's style remain shared. Evaluation stayed procedurally sealed until its advisory protocol was recorded; it was not independently authored or sampled from real incidents.

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

Actual requests, raw replies and local fitted explanations stay in immutable ignored run directories. The read-only workbench derives policy traces from those verified readings. Tracked checkpoints summarize measured evidence; a fresh clone without the runs must show missing predictions explicitly.

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

The [candidate freeze](../checkpoints/task-fit-candidate-2026-10-03.json) selects **Structured** using the predeclared development rule. Its question and input construction stay unchanged for calibration. At reader selection, no operating threshold was selected. The subsequent advisory boundary and held-out result are recorded below. Operational use still requires specialist-reviewed examples and explicit acceptable-error and useful-coverage targets.


## Calibration and review coverage

The frozen Structured reader completed all 24 calibration calls without failures, matching 23/24 report references and 23/24 packet references. The study now contains 192 actual hosted calls: 96 primary, 72 repeated and 24 calibration. [Calibration evidence](../checkpoints/task-fit-calibration-2026-10-03.json).

Its one error is report `NTF-80984668148c-b`:

> Instrument domain: power. Before repair the regulator was faulty. The current exercised-load measurement verifies output within its declared range.

Jev returns `fault` with probabilities 0.51 fault, 0.48 normal and 0.01 unknown. The draft reference is `normal` because the current measurement verifies the repaired regulator. The frozen policy consequently recommends power rather than retaining NOC. This error concerns the reading, not a missing domain declaration or service path.

| Minimum returned-reading probability | Accepted readings / 24 | Reading errors among accepted | Domain recommendations / 24 | Wrong domain recommendations | Readings in review |
|---|---|---|---|---|---|
| 0.50 | 18 | 1 | 10 | 1 | 6 |
| 0.60 | 16 | 0 | 9 | 0 | 8 |
| 0.90 | 13 | 0 | 7 | 0 | 11 |
| 0.99 | 10 | 0 | 5 | 0 | 14 |

An accepted reading is a fault or normal answer that meets the displayed threshold. A domain recommendation also requires the unchanged policy to identify a domain team with sufficient evidence. Confident normal readings can still leave NOC investigating a degraded service. At 0.60, therefore, 16 readings qualify but only nine incidents receive a domain-team recommendation. The remaining 15 incidents retain NOC or require review; those outcomes do not all imply an uncertain report reading. The [supplementary routing calculation](../checkpoints/task-fit-routing-review-2026-10-03.json) preserves every saved prediction and score.

The threshold sweep describes this pack. It does not establish a safe operating threshold: even 16 independent accepted readings with zero errors would give an approximately 17% one-sided 95% upper error bound. These reports are paired, making that independence assumption optimistic. Raising the threshold also discards correct readings; the study does not yet establish whether that tradeoff helps analysts.

Multiclass Brier score is 0.0450 and log loss is 0.0891 on these 24 reports. Median client latency is 146 ms and the 95th percentile is 181 ms. Provider-reported usage is 11,703 input and 912 output tokens. These measurements neither validate operational calibration nor determine billed cost.

## Inspect the study

Open `/task-fit` in the app. Its five steps connect the comparison table, paired reports, exact saved Jev request, actual response and software policy, then the probability sweep. Inspection makes no hosted calls. References stay hidden until revealed; missing raw runs remain explicitly unavailable on a fresh clone. The historical public bundle does not include this study.

Start with the development timing report above in Prose, reveal its reference, then select Structured to see the changed state and corrected reading. Switch to Calibration and the repaired-regulator report to inspect the remaining failure. The coverage table distinguishes accepted readings from domain recommendations at each threshold. The experiment guide returns to the selected case and arm.

## Analyst-facing evaluation and next step

The user selected analyst-facing recommendations on October 3. Preparation commit `3f3c8b8` records the [advisory protocol](task-fit-analyst-evaluation.md): a calibration-selected 0.60 display threshold and author-set provisional research criteria, frozen before evaluation. Every report requires analyst review. No operational error budget or automatic routing is approved.

All 24 held-out calls completed without failures. The reader matches 21/24 report references and 22/24 packet references. At frozen threshold 0.60, 17 readings qualify and nine domain suggestions include one wrong core suggestion at probability 0.84. The candidate fails the zero-error research criteria. The completed evaluation is now inspectable at `/task-fit`; the advisory guide explains all three reading errors and the fixed assessment.

I would retain Jev as an analyst-assistance candidate, with the evidence visible and every suggestion reviewed. These results do not establish a fair ranking against a sufficiently trained ML reader or reliable confidence-qualified assignments. Explicit function definitions are a concrete next input test on new development families. Changing the boundary after seeing the held-out errors would invalidate this evaluation as a selection-independent check.

The [analyst review plan](analyst-review-plan.md) prepares specialist review and a local batch of real reports. Those reports, reviewed reference meanings and measured analyst effort are not available yet. Further synthetic cases can test input design but cannot establish operational task fit. Idle-handler semantics remain deferred.
