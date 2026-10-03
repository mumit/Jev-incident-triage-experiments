# Current study baseline

October 1, 2026. This is the starting point for experiment 3. The `checkpoints/study-baseline-2026-10-01.json` records the application source, dataset, settings and results. Its verification reads saved files and recomputes scores without fitting models or calling Jev.

## What is complete

Two experiments compare Rules, ML · original, ML · revised, Jev · original and Jev · focused. Every approach selects an investigating team, priority, next diagnostic and evidence sufficiency under the fictional Northstar Telecom policy.

The app supports saved comparisons, eight walkthrough chapters, exact Jev request inspection, ML score reconstruction, paired cases and a local evidence sandbox. The study reader renders Markdown with section navigation, expandable tables, copyable code and links into case inspection.

Experiment 3 has not started. The lab recommends diagnostics; it does not execute network changes. Its observations describe abnormalities, rather than raw KPI time series.

## Fixed references

| Reference | Version or location |
|---|---|
| Application before stocktake | `98f5c9d4fbad909806f4ffd788bbde2a449f9e17` |
| Source including audit tooling | `84e414ae663f803204c87078de41a816cb71a6ac` |
| Experiment 2 inference checkpoint | `6a44f62`; four file hashes in the freeze record |
| Jev requested and returned checkpoint | `jev-1.13.0` in both experiment 2 variants |
| Historical evidence | Public `study-evidence-v1` release, with four runs and a freeze record |
| Current comparison checkpoint | `checkpoints/study-baseline-2026-10-01.json` |

The checkpoint fingerprints 28 application, audit, dependency and launcher files; nine dataset files; and 67 historical evidence files. It includes recomputed summaries for 18 approach results across four runs. JSON metadata paths become repository-relative and formatting is normalized, so release restoration and the original local evidence can be compared. Prediction and input JSONL bytes remain exact.

The four frozen inference files are `experiments.py`, `ml.py`, `runner.py` and `policy.py`. Their current hashes match the freeze record. That record applies to experiment 2; experiment 1 predates the revised representations and response handler.

Raw runs remain ignored. The checkpoint contains audited summaries, hashes and a few error identifiers; the [release bundle](run-bundle.md) supplies the predictions and responses needed for a full audit. Credentials, current session settings and personal filesystem paths are excluded.

## Data and methods

| Dataset | Packets | Scenario families | Role |
|---|---:|---:|---|
| Training | 600 | 30 | Fits both ML variants |
| Validation | 220 | 11 | Guided experiment 2 revisions |
| Test | 220 | 11 | Checks the frozen revisions |
| Challenge | 24 | 4 types, 12 pairs | Tests controlled input changes |

The 11-packet learning set belongs to validation. Regular families have 20 correlated variations. Training, validation and test family IDs are disjoint, but wording and network patterns can recur. Five test packets and four challenge packets appeared in earlier runs. Subsequent review exposed their failures, so they cannot provide an untouched evaluation for further tuning.

| Approach | Representation and method |
|---|---|
| Rules | Observation keywords, fixed routing and exact impact-priority calculation |
| ML · original | Original policy-and-incident state; word TF-IDF and four logistic classifiers |
| ML · revised | Compact state; word/character TF-IDF and structured impact; impact-only priority classifier |
| Jev · original | Original state and short Choice definitions |
| Jev · focused | Compact state and explicit independent task definitions |

Both ML variants fit only the original 600 training packets. The original ML/Jev pair shares the original state; the revised ML/focused Jev pair shares the compact state. Neither receives labels, family IDs or generation metadata during inference. Jev received no telecom fine-tuning in this study.

The checkpoint records each run's policy and question fingerprints, request variant, declared context, ML training fingerprints, parameters and scikit-learn version. Hosted runs declared 32,768 context tokens. Both experiment 2 Jev variants used the bounded probability-rounding handler, which retains raw values and does not alter selected answers.

## Recorded results

All-four accuracy requires every decision to match an accepted reference. Failed and missing responses count as errors.

| Approach | Validation | Test | Challenge | Both challenge packets correct |
|---|---:|---:|---:|---:|
| Rules | 90.9% | 90.9% | 87.5% | 75.0% |
| ML · original | 58.6% | 59.5% | 16.7% | 0.0% |
| ML · revised | 86.4% | 96.8% | 58.3% | 50.0% |
| Jev · original | 50.9% | 57.7% | 79.2% | 58.3% |
| Jev · focused | 100.0% | 90.9% | 87.5% | 75.0% |

The audit reproduced every saved metric in all four runs. A fresh local clone restored the public evidence bundle and matched the same source, data, evidence and result fingerprints. Experiment 2 has zero failed or missing responses. Experiment 1 retains five probability-format failures in its Jev validation run. Metrics absent from that older run remain null in the checkpoint, rather than being presented as historically recorded results.

Priority accounts for much of the improvement. With the separate software-priority calculation, original Jev's test score rises from 57.7% to 90.9%, and original ML's from 59.5% to 79.1%. Revised ML learned its priority mapping from training labels. Neither score explains which bundled experiment 2 change caused a semantic improvement.

## Failures to carry forward

| Approach and evaluation | Recorded weakness |
|---|---|
| Jev · focused, test | All 20 neighbour-change variations select a different diagnostic from the reference; owner and evidence disposition are correct. The diagnostic reference needs specialist review. |
| Jev · focused, challenge | Three changed-dependency packets miss owner, diagnostic and evidence disposition. All three owner errors assign at least 80% probability to the wrong choice. |
| ML · revised, validation | Maintenance-scope cases still miss the diagnostic and evidence decision, and revised ML introduces owner errors. |
| ML · revised, test | Six owner errors and seven diagnostic errors in the transport-direction family |
| ML · revised, challenge | Six dependency cases and four stale-evidence cases miss owner/diagnostic decisions; six evidence-sufficiency errors across these two types |

The [measured review](performance-review.md) links individual cases. Scores describe constructed teaching scenarios, not operational accuracy. Model probabilities are uncalibrated, reference diagnostics can be ambiguous, and latency reflects the recorded machine and serial hosted execution rather than a throughput test.

## Compare future changes

Preserve this checkpoint and the released evidence. Store new runs under new IDs, and capture later checkpoints in new files.

A direct score comparison requires identical evaluation input and answer-key hashes and the same policy. The comparison command also lists changes to questions, model identity, context, training and other recorded settings. Those changes need explanation before attributing a gain. Multiple simultaneous changes cannot establish which one caused it.

New scenario families require a fresh baseline and changed variants evaluated on the same new cases. Their absolute scores can be shown beside the historical study for context, but their difference is not a measured improvement over the historical dataset. Keep historical model replay separate from ML variants retrained on the new training split; fit all competing new ML variants on that same split.

### Verify this baseline

```bash
uv run --locked python -m scripts.study_checkpoint verify checkpoints/study-baseline-2026-10-01.json
```

The report distinguishes changed files from missing evidence and checks saved summaries against recomputed results. A fresh clone needs the [historical bundle](run-bundle.md) for the evidence checks. A mismatch exits with status 1; inspect it rather than rewriting the baseline. Later application changes may be intentional even when inference and data still match.

### Compare a saved run

```bash
uv run --locked python -m scripts.study_checkpoint compare checkpoints/study-baseline-2026-10-01.json --reference test --run runs/app/3739acf583a64c79
```

This self-comparison reports zero score changes. Substitute a new run directory for an actual comparison. Different data or policy suppresses score deltas; changed settings remain visible. The command currently recognizes the five existing approach identifiers. New experiment 3 identifiers need explicit reference mappings before comparison.

### Capture a later checkpoint

Commit matching application changes first, then use a new output filename and the local capture date:

```bash
uv run --locked python -m scripts.study_checkpoint capture checkpoints/study-baseline-next.json --as-of YYYY-MM-DD
```

The current capture selection remains the four historical runs. Register new experiment run IDs before capturing their results. The tool refuses to overwrite a checkpoint and checks that application files match the stated source commit.

## Immediate next task

Prepare independent dependency and measurement-age transformations, new development families and a reviewable inspection flow. Keep Jev's checkpoint, questions and decision policy fixed for the first input comparisons. Train the new ML baseline and feature variants on the same new training split. Specialist review and frozen answer keys come before final evaluation; hosted calls follow a bounded development run plan.

I will use the familiar failures to design that work, then evaluate frozen changes on separate families. Read-only diagnostic tools depend on those results. Raw KPI anomaly detection remains a separate experiment.

## Development after this checkpoint

The [experiment 3 development guide](experiment-3-development.md) records the new draft pack, local pilot and completed 144-request Jev comparison. That work changes application source while preserving the historical data and evidence recorded here. This checkpoint remains the pre-experiment-3 baseline; it does not capture the new pilot.

The subsequent [question-precedence trial](experiment-3-question-precedence.md) uses a further separate draft pack and matched questions on identical states. It also preserves this historical baseline.

The subsequent [conflict repetition](experiment-3-conflict-repetition.md) adds a further development pack and repeated fixed requests. It preserves the pre-experiment-3 baseline recorded here.

The subsequent [evidence-selection comparison](experiment-3-evidence-selection.md) adds 12 further development packets and preserves this historical baseline. Its matched input scores do not replace any result recorded in the stocktake.

The [selection-robustness check](experiment-3-selection-robustness.md) completed 48 calls on eight new packets, repeating both frozen inputs three times. Selected observations match all eight draft references in every repeat; combined facts match seven. Selection fixes one validity-boundary packet, repeated three times, and introduces no new wrong fields. Both inputs pass the partial-inventory, missing-inventory and multiple-domain controls and keep identical decisions across repeats. The multiple-domain reference remains provisional; agreement does not establish correctness or operational reliability. This work preserves the pre-experiment-3 historical checkpoint; its new report is separate.

The [structured ML comparison](experiment-3-structured-ml.md) fits four matched classifiers on 96 new training packets and scores 64 development packets. Both feature blocks together match 52/64 draft references versus 24/64 for the text baseline, with 20/32 versus 6/32 pairs correct. It fixes 28 complete packets and loses none, but introduces eight wrong owner fields and ten wrong diagnostic fields on already-failed packets. Current transport faults still receive NOC at about 85% probability. Jev makes no calls in this comparison. The historical stocktake and its evidence remain unchanged.

## Training-wording comparison, October 2

The [training-wording comparison](experiment-3-wording.md) is complete on 80 new development packets. Counterbalancing “tests” and “diagnostics” weakens their method-word weights but scores 61/80 against 64/80 for matched coupled wording. It fixes one packet and loses four, with new owner, diagnostic and evidence errors. The original training bridge scores 65/80. The original combined candidate stays unchanged.

## Report-policy comparison, October 2

The [report-policy study](experiment-3-interpretation.md) compares a text-only report classifier and explicit report rules feeding the same fixed policy. Separate report annotations describe domain and fault/normal/unknown meaning, independent of packet decisions. On 108 new development packets, Report ML scores 62/108 against 55/108 for matched packet ML and 70/108 for the previous frozen candidate. Report rules match all draft references on this simple authored pack. Inspect the report readings, policy traces and fitted contributions at **Comparison → Report interpretation and policy**. No Jev calls were made. The tracked checkpoint is `checkpoints/experiment-3-interpretation-2026-10-02.json`; the original stocktake and historical runs remain unchanged. The subsequent [report-language study](report-language.md) records that intervention and a Jev architecture comparison.


## Report-language continuation

The [report-language comparison](report-language.md) uses 186 matched training packets, 210 annotations and 140 new development packets. Broader phrases score 86/140 against 90/140 for original report phrases: four fixes and eight regressions. On the same pack, Jev report interpretation feeding fixed policy scores 139/140 against 127/140 for frozen direct triage, fixing 13 packets and losing one. Jev misreads five core acceptance reports, four hidden by correct triage. These are draft-reference development results. The user subsequently selected acceptance as normal for the measured handler, with completion assessed separately.

## Measured-function question result

The [matched reading-instruction comparison](report-scope.md) completed 176 Jev calls on 68 further development packets and 88 reports. Added scope guidance changes report agreement from 82/88 to 83/88 and packet agreement from 67/68 to 68/68, with two report fixes and one loss. Five wrong readings remain hidden by correct triage, including both predeclared function-comparability policy gaps. Frozen ML controls score 46/68 packets while transferring poorly to the new wording. Inspect `/report-scope`; measurement-scope provenance needs a decision before the next policy comparison.
