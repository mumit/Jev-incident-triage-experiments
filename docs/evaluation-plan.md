# Evaluation plan

The evaluation compares four incident decisions under the [fictional policy](policy.md). [The measured review](performance-review.md) records the completed experiment 2 runs. This plan separates implemented scoring from future work.

## Task and inputs

The outputs are `initial_owner`, `priority`, `next_check` and `insufficient_evidence`. Correctness uses the accepted answers in the separate key. Selecting an initial team does not establish a root cause or authorize a network change.

In experiment 1, original ML and original Jev receive the same allowlisted policy-and-incident state. In experiment 2, revised ML and focused Jev receive the same compact state. Revised ML also derives structured impact features from that state; focused Jev receives more explicit questions. Rules read observations and impact. No approach receives reference labels, family IDs or generation metadata during inference.

In experiments 1 and 2, each ML vocabulary and classifier fits only the 600 original training records. Experiment 3 fits its four matched variants only on the 72 new training packets. Jev uses the fixed hosted checkpoint `jev-1.13.0`, without telecom fine-tuning in this study. These approaches have different training histories.

## Implemented scores

| Measure | Definition |
|---|---|
| All four decisions correct | Every field matches an accepted reference. Failed and missing responses count as failures. |
| Three semantic decisions | Owner, next check and evidence sufficiency match; priority is excluded. |
| With software priority | The three model decisions match, and the separately calculated policy priority matches. Failed responses remain failures; saved predictions stay unchanged. |
| Field accuracy and macro-F1 | Each decision is scored separately, with confusion matrices and error entries. |
| P1 miss rate | Incorrect priority among P1 reference packets. Undefined when the set has no P1 cases. |
| Both packets correct | Every decision matches on both sides of each challenge pair. |
| Brier score and reliability bins | Candidate-answer probabilities are compared with a unique reference. Brier scoring skips fields with multiple accepted answers. |
| Coverage curves | Error and fraction retained at fixed selected-answer probability thresholds. These are descriptive curves, not calibrated permissions for automation. |
| Family bootstrap intervals | Resample scenario families rather than treating their variations as independent incidents. |
| Median and p95 latency | Successful calls only. Local latency includes feature transformation and prediction; hosted latency includes network and serving time. ML fitting time is recorded separately. |
| Failure and usage records | Attempted, failed and missing responses; returned model identity, usage and probability-adjustment metadata where available. |

Jev's provider confidence is separate from its candidate-answer probabilities. Common probability scores use the latter. Rules return decisions without probability distributions. Missing probabilities and predictions remain explicit.

## Completed experiment controls

I fixed the original ML settings before validation. Validation failures guided the revised ML features and focused Jev requests; the inference source remained frozen throughout the full test and challenge runs. Both Jev variants used the same updated response handler, which normalizes only bounded rounding drift and retains raw values.

The 11 learning packets already belong to validation. Training, validation and test families are disjoint, but repeated wording and network structures can recur. Five test packets and four challenge packets appeared in earlier runs, so the full checks were not entirely unseen.

Each regular evaluation set has 11 families with 20 correlated variations per family. The challenge has four types and 12 pairs. This sample does not establish real incident frequencies, production calibration, operational savings or model superiority.

## Next experiment

The [experiment 3 development pilot](experiment-3-development.md) now compares four matched ML/Jev input variants on 36 paired packets: compact baseline, dependency facts, measurement age and both. The new references remain drafts. The policy, questions and Jev checkpoint are unchanged, and all four classifiers fit only the same new training split. Jev completed all 144 requests with zero failures; neither added fact block improves its aggregate score. [The reference review](experiment-3-reference-review.md) identifies question/reference ambiguities. Further revisions need new development families. No final held-out set exists.

Before evaluating separate families, I will freeze the transformations and questions. The evaluation will retain all four outputs, score software priority separately and include a review of high-probability errors. Network specialists will review ambiguous diagnostic references before I freeze the answer keys. See [the overview](experiment-overview.md#next-experiment).

Threshold selection, operational calibration, cost estimates, throughput tests and raw KPI anomaly detection remain future work. The existing coverage curves do not validate an automation threshold.

## Before publishing results

Check split-family separation, input/answer-key isolation, timestamp availability, paired interventions and checksums. Verify reported scores against the saved runs and record the input, question, training and source fingerprints. Keep credentials out of tracked files and exports and use the fictional operator identity throughout.

Historical runs remain local and ignored by Git. The repository includes their measured reports; a fresh clone does not contain the raw evidence needed to re-audit those historical predictions. See [verification](verification.md).

The [question-precedence trial](experiment-3-question-precedence.md) completed 32 requests on 16 further development packets. Its two arms share the same combined state, checkpoint, policy, valid choices and priority question. Only three question instructions differ. References reflect the user-selected NOC teaching rule but remain unreviewed by a network specialist. Scores are matched within this trial; do not compare them as deltas from the earlier pack. Single-response variation and the remaining owner regression need further checks.

The [conflict repetition](experiment-3-conflict-repetition.md) repeats eight distinct packets three times under each frozen question set. Report per-repeat scores and packet-level agreement. Planned response counts remain in the denominator; repeated responses do not increase the number of independent cases. Further revisions require new development cases.

The [evidence-selection comparison](experiment-3-evidence-selection.md) keeps explicit questions fixed on 12 further packets, comparing combined facts, added eligibility facts and eligible-only state. Report complete-packet and field fixes, regressions and pair correctness. One call per packet/input cannot establish variability. Selection retains current-conflict controls and tests empty eligible sets; further development cases must check filtering assumptions before final held-out evaluation.

The [selection-robustness check](experiment-3-selection-robustness.md) completed 48 calls on eight new packets, repeating both frozen inputs three times. Selected observations match all eight draft references in every repeat; combined facts match seven. Selection fixes one validity-boundary packet, repeated three times, and introduces no new wrong fields. Both inputs pass the partial-inventory, missing-inventory and multiple-domain controls and keep identical decisions across repeats. The multiple-domain reference remains provisional; agreement does not establish correctness or operational reliability.

The [structured ML comparison](experiment-3-structured-ml.md) fits four matched classifiers on 96 new training packets and scores 64 development packets. Both feature blocks together match 52/64 draft references versus 24/64 for the text baseline, with 20/32 versus 6/32 pairs correct. It fixes 28 complete packets and loses none, but introduces eight wrong owner fields and ten wrong diagnostic fields on already-failed packets. Current transport faults still receive NOC at about 85% probability. Jev makes no calls in this comparison.

The [training-wording comparison](experiment-3-wording.md) is complete on 80 new development packets. Counterbalancing “tests” and “diagnostics” weakens their method-word weights but scores 61/80 against 64/80 for matched coupled wording. It fixes one packet and loses four, with new owner, diagnostic and evidence errors. The original training bridge scores 65/80. The subsequent [report-policy study](experiment-3-interpretation.md) is complete on 108 further development packets. Report ML gets 62/108 right versus 55/108 for matched packet ML and 70/108 for the previous frozen candidate. Its report readings fail despite correct domain choices. The completed [report-language study](report-language.md) records that matched intervention and a Jev architecture comparison on 140 further development packets. Specialist review still precedes final held-out evaluation.

The exact-request diagnostic replay repeats four inspected report texts three times; those 12 responses are not independent cases. Preserve the original 140-packet scores. [The reference decision brief](report-language-review.md) records the user-selected normal handler boundary. Version changes rather than relabeling recorded evidence.

The completed [measured-function instruction comparison](report-scope.md) uses separately prewritten report annotations and 68 further development packets. Two policy gaps were declared before calls. Scores must distinguish report correctness, triage correctness and incorrect readings hiding policy errors. Any scope-aware policy change needs a separate matched comparison, new families and an explicit source for measurement scope.
