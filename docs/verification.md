# Verification

October 2, 2026. This document records the current implementation checks and their limits. [The measured review](performance-review.md) records experiment results; [the overview](experiment-overview.md) explains the study.

## Automated checks

The working checkout passes **132 Python tests and nine JavaScript tests**. Dataset validation confirms 600 training, 220 validation, 220 test and 24 challenge packets. All four browser scripts pass syntax checks, and the launcher passes its shell syntax check.

The checks cover:

- Train-only ML fitting, shared allowlisted states and exclusion of labels and generation metadata from inference.
- Failure-inclusive scoring, separate software-priority scoring, controlled pairs and bounded probability normalization.
- Request construction, local HTTP fixtures, configuration secrecy and credential exclusion from errors and exports.
- Exact reconstructed Jev request hashes for the three full saved runs and unchanged frozen inference source.
- Binary and multiclass ML score reconstruction, impact-only priority features and training-only neighbours.
- Local sandbox isolation: no hosted Jev calls, input mutation, answer-key reuse or saved-run changes.
- Family/failure filter selection, empty matches, browser navigation state and delayed-response handling.
- Explicit separation between a local ML replay and a missing saved or hosted prediction.
- Study rendering, safe Markdown, local return links, document allowlisting, original source downloads and article routes.
- Bundle credential rejection, unexpected archive paths, payload checksums and restoration that refuses conflicting evidence or symlink destinations.

Run the checks in [the README](../README.md#checks). Two Python tests require local historical runs: exact saved-request hash matching and saved provider-response export allowlisting. They skip on a fresh clone; the other tests still exercise request construction, secrecy and export routes.

## Browser review

The browser review covered all eight walkthrough chapters at wide, tablet and phone widths, including a 390-pixel viewport. Checks also covered the comparison lab, its connection to the walkthrough and the settings dialog. The pages did not spill horizontally; wide comparison tables scroll within their containers. Browser error logs were empty.

The reviewed flows include:

- Formatted study articles at wide, tablet and 390-pixel widths, section navigation, table expansion, exact code copying and readable reference guides.
- Study return links restoring the selected packet, approach, field, inspection view and chapter; Markdown downloads preserve the source.
- Four separately stated decisions and a guided tour that starts with the radio scheduler validation case.
- Narrow-screen chapter selection, family selection, failure filters, empty states and previous/next movement.
- Evidence, decisions and model inspection, with a separate paired-input view and browser Back restoring the previous case or step.
- Hidden references, missing saved training predictions and explicitly labelled local ML replay probabilities.
- Exact Jev requests, raw returned answers, response audits and selectable JSON export dialogs.
- ML score reconstruction, alternative-class comparison, feature search and expansion from 15 to 50 visible contributions.
- Paired graphs, individual-field scores and pair scoring restricted to the challenge set.
- Before/after sandbox decisions at nine and ten sites, preserved edits, stale-result notices and disabled counts for unknown/no impact.
- Saved results before optional new-run setup; key entry first in settings, expandable connection details and a visible Save action.

## Experiment integrity

The four inference files still match `runs/performance-freeze.json`: `experiments.py`, `ml.py`, `runner.py` and `policy.py`. The walkthrough and UX work did not change the frozen dataset, reference answers, predictions or inference behavior. Interface work and checks ran locally without hosted Jev calls.

The experiment 2 validation, test and challenge runs completed with zero failed or missing responses. The first experiment's validation run had five response-validation failures, which count against its score. These were probability-format failures, not evidence of a selected decision's quality.

## Repository boundary

The GitHub repository contains source, the synthetic dataset, separate answer keys and measured reports. It excludes `.env`, raw `runs/`, local virtual environments and generated caches. Historical predictions and the freeze record remain in the working checkout.

A fresh clone can inspect data and policy, fit local ML, reconstruct local scores and use the sandbox. It cannot show the historical comparisons or confirm historical hashes without the recorded run files. Missing results remain explicit. Newly created app runs do not replace the walkthrough's fixed experiment run IDs.

The checks establish the behavior of this teaching tool. They do not certify scenario realism, diagnostic references, probability calibration, operational reliability or savings.

## Historical evidence release

The `study-evidence-v1` release provides the four documented synthetic runs and freeze record as an archive outside Git history. Its manifest binds the evidence to a source commit, dataset fingerprints and per-file checksums. Metadata paths become repository-relative; prediction rows and returned responses remain unchanged. [The bundle guide](run-bundle.md) explains restoration, and [HANDOFF.md](../HANDOFF.md) describes the next task.

A fresh local clone restored the archive and passed all 45 Python tests without skips. Rebuilding the measured review from those restored runs reproduced the committed report exactly. Restoration did not require a Jev key or make hosted calls.

## October 1 baseline audit

The [current-state checkpoint](current-state.md) matches 28 source files, nine dataset files and 67 portable evidence files. Recomputed scoring reproduces all saved metrics for 18 approach results across four runs. A self-comparison of the recorded test run reports zero score changes. Five additional tests cover checkpoint overwrite refusal, changed versus missing files, portable metadata, edited summaries and suppression of score deltas for different inputs, answer keys or policy.

A fresh local clone of the audit source restored the public v1 evidence bundle and passed the baseline verification, including all 18 recomputed approach results. Metadata normalization makes its fingerprints match the original checkout without exposing personal paths.

## Experiment 3 development checks

Eighteen new Python tests cover transformation isolation, identical questions, measurement/report age, boundary and unknown statuses, impossible timestamps, directional paths, partial maps and cycles. They also check draft pair integrity, reproducible generation, train-only fitting, matched settings, run overwrite refusal, source drift, recomputed scores and local HTTP request exports. The new validator confirms 72 training and 36 development packets.

Browser inspection covered raw evidence, calculated facts, exact input and decisions, paired topology changes, stale measurement with recent arrival, missing topology, hidden draft references, probabilities and unscored training packets. The app's local replay completed without hosted calls. Desktop, 820-pixel and 390-pixel layouts were checked; a topology-diff overflow was corrected. Request copying produced success feedback. A server-backed JSON download completed, and its parsed body matched the exact prepared request. A fresh data-only fixture exposed inputs and prepared requests without inventing local or Jev results.

The baseline audit still matches all nine historical data files, 67 evidence files and 18 recomputed approach results. It reports the intended changes to five application files. The four frozen inference files are unchanged. New local pilot scores use draft references and are separate from historical comparisons; the app verifies saved input, training, source and prediction fingerprints and recomputes scores before displaying them.

## Experiment 3 hosted development checks

Eleven additional Python tests cover context and checkpoint preflight, rotated serial execution, overwrite refusal, exact requests saved before inference, credential redaction, rate-limit and malformed-response stops, failure-inclusive scoring, request/source fingerprints and rejection of edited metrics. Partial-run checks keep missing development responses and unscored training packets explicit.

The first hosted comparison completed 144 requests with zero failures. Every response reported `jev-1.13.0`. The app verifies the saved protocol, input and reference checksums, exact requests and prediction fingerprints, then recomputes every score before displaying results. The tracked hosted report matches that saved evidence. These checks establish recording and scoring integrity; they do not validate the draft references.


Browser checks covered all nine result rows, selected ML/Jev variants, hidden and revealed draft references, exact request copying and downloading, matching saved request/response hashes, returned probabilities and unscored training packets. The stale-measurement case exposed a one-minute report age alongside a 95-minute measurement age. Desktop, 820-pixel and 390-pixel layouts had no page overflow; wide tables scroll within their containers. The new review article and hosted report links worked, and browser error logs were empty.

## October 2 question trial

Nine new Python tests check reproducible fresh families, six decision-changing and two invariant pairs, identical states and priority questions, input allowlisting, question fingerprints, serial ordering, prewritten requests, credential redaction, stop conditions, failure-inclusive scoring, edited-metric rejection and read-only inspection/export routes. A data-only fixture shows missing predictions explicitly and rejects training inspection for this development-only pack.

The hosted trial completed 32 requests with zero failures; every response reported `jev-1.13.0`. Saved source, request and data fingerprints match, and recomputation reproduces both score sets. The original 144-request run still verifies unchanged. These checks establish the controlled comparison and evidence recording; they do not validate references or probability calibration.

Browser review covered the comparison selector, exact original/revised question definitions, a corrected unrelated-fault packet, the remaining stale-conflict owner regression, reference reveal, copied and downloaded requests and the formatted results article. The selected JSON download matched the recorded request. Desktop, 820-pixel and 390-pixel layouts had no page overflow; tables scroll inside their containers. Browser error logs were empty.

## Repeated conflict checks

Six new tests cover reproducible new conflict families, identical requests across three planned repetitions, the complete master plan saved before inference, response variation, credential redaction, rate-limit stops across the study, failure-inclusive denominators, edited-summary rejection, repetition selection, missing-result fixtures and exact HTTP request exports. The validator confirms eight distinct packets in four decision-changing pairs.

All 48 hosted requests completed with zero failures and reported `jev-1.13.0`. The app recomputes child scores and master response/agreement summaries before displaying them. Source, request and data fingerprints still verify the previous 144-request and 32-request runs. The historical baseline's data, evidence and recorded results remain unchanged. These checks do not validate synthetic references, instrument thresholds or general reproducibility.

Browser review covered all three repetitions, the variable load-panel diagnostic, timestamp indexing, draft-reference reveal, exact request downloads and both earlier comparisons. The downloaded JSON matched the prepared request. Desktop, 820-pixel and 390-pixel layouts contained the tables without page overflow; browser error logs were empty. The guide's return action now preserves the packet, question arm, repetition and inspection step, with the local-route guard checked in the reader tests.

## Evidence-selection checks

Eight new tests cover fresh paired data, eligibility on partial/unknown/excluded relationships, measurement-time validation, validity boundaries, raw-packet preservation and consistent reindexing. They check retention of current contradictions, empty evidence, identical frozen questions, the historical combined baseline, input allowlisting, rotating order, complete request recording, immutable runs, credential redaction, rate-limit stops, response-file tamper rejection and exact HTTP exports. Data-only fixtures show missing results explicitly. The validator confirms 12 packets in six further families and pairs.

All 36 hosted requests completed with zero failures and reported `jev-1.13.0`. Recorded data, source and request fingerprints verify; response-file hashes and recomputed scores match. Frozen historical inference and data remain unchanged; the baseline audit records the intended app and reader changes. These checks establish implementation and evidence integrity, not scenario realism, reference validity or operational reliability.

Browser review covered all three inputs, raw-to-request index mapping, current-conflict retention, unknown-time removal, partial field improvements and draft-reference reveal. Copying showed success feedback; downloaded JSON matched the prepared request. The reader returned to the same case/input/step and linked to the recorded report. Desktop, 820-pixel and 390-pixel layouts showed no page overflow; browser error logs were empty. The earlier repetition view retained its saved results. Hidden controls now stay hidden outside their comparison, and guide links update when the selected packet or input changes.

## Selection-robustness checks

Seven new tests cover reproducible families, the invariant inventory-coverage pair, inclusive validity boundaries, visible paths with partial inventory, empty eligible sets and retention of multiple current domains. They check identical questions and the historical combined input, all 48 requests planned before inference, three identical repeats, response variation, credential redaction, rate-limit stops, planned denominators, edited-summary rejection, immutable inspection snapshots, missing-result fixtures and exact HTTP exports. The validator confirms eight packets in four further families.

All 48 hosted requests completed with zero failures and reported `jev-1.13.0`. Child and master fingerprints and recomputed scores verify; the tracked report matches the recorded summary. All earlier experiment 3 runs still verify. The historical audit finds only the intended app and reader source changes; its nine data files, 67 evidence files and 18 recorded result checks remain unchanged. These checks establish evidence integrity, not operational accuracy or valid diagnostic references.

Browser review covered all repetitions, the one-second boundary, partial-path retention, missing-inventory removal, provisional multiple-domain references and both exact inputs. Copy feedback appeared and the downloaded JSON matched the prepared request. The guide linked to its report and returned to the same packet, input, repetition and step. Desktop, 820-pixel and 390-pixel layouts showed no page overflow; browser error logs were empty. The earlier selection view retained its saved scores.

## Structured ML checks

Nine new tests cover reproducible data, single-field pairs, disjoint families, input/reference isolation, observation-bound categories, reordering, unknown evidence and train-only vocabularies. They check identical impact-only priority probabilities, preservation of the earlier compact baseline recipe, complete log-odds reconstruction, immutable runs, evidence tamper rejection, missing-result inspection, feature-only HTTP exports and rejection of local training routes for hosted-only studies. A separate check counts newly wrong fields on packets already failed by the baseline.

All four local fits completed on 96 training packets and scored 64 development packets. Recorded inputs, predictions, vectors and explanations verify. Every saved explanation reconstructs its probability margin from the intercept, shown contributions and remaining contribution. The tracked report matches the run and independently calculated fixes/regressions. Seven dataset validators pass; all earlier saved runs remain unchanged and verify. These checks establish implementation and evidence integrity, not operational accuracy, calibration or representative scenario coverage.

Browser review covered feature-set and probability-field selection, observation channels, nonzero vectors, draft-reference reveal and training packets without evaluation predictions. Copy feedback appeared; downloaded JSON matched the exact saved feature bundle. The guide linked to its report and preserved the case, arm and inspection step on return. Desktop, 820-pixel and 390-pixel layouts showed no page overflow; browser error logs were empty. The workbench reports field regressions alongside complete-packet gains.

## Training-wording checks

Eight new tests cover reproducible matched data, unchanged training targets, single-field pairs, exact method-word counts, identical development inputs and synonym controls. They verify the frozen feature settings, shared impact-only priority, input/reference isolation, train-only vocabularies, immutable runs, evidence tamper rejection and field regressions on already-failed packets. Missing-run fixtures expose actual training wording without fabricated predictions. HTTP exports preserve the selected training arm, and the reader links to the recorded report. Agreement and correctness have separate denominators.

All three local fits completed on 96 training packets each and scored the same 80 development packets. The recorded report matches the saved run and independently recomputed control scores. Source and data hashes, vectors, method-word weights, score margins and matched changes verify. Eight dataset validators pass, and all earlier recorded sources and evidence still verify. These checks establish implementation and evidence integrity, not valid references, calibration or operational accuracy.

Browser review covered all three training wordings, actual report substitutions, development predictions, probability fields, feature channels, a new owner regression and training packets without evaluation results. Copy feedback appeared and downloaded JSON matched the selected input and saved vector. The formatted guide linked to its report and returned to the same case, arm and inspection step. Desktop, 820-pixel and 390-pixel layouts had no page overflow; tables scroll within their containers. Browser error logs were empty, and the earlier structured comparison retained its saved scores. Pair rationale is now explicitly labeled A-to-B, alongside the reference for the selected packet.
