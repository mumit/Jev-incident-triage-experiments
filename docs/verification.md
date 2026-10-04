# Verification

October 3, 2026. This document records the current implementation checks and their limits. [The measured review](performance-review.md) records experiment results; [the overview](experiment-overview.md) explains the study.

## Automated checks

The working checkout passes **222 Python tests and nine JavaScript tests**. Dataset validation confirms 600 training, 220 validation, 220 test and 24 challenge packets. All ten browser scripts pass syntax checks, and the launcher passes its shell syntax check.

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

## Report-policy checks

Ten new tests cover reproducible data, separate report annotations, stale faults that retain their report meaning, input/reference isolation and train-only vocabularies. They verify policy joins, current contradictions, visible paths, missing relationships, negation and uncertainty precedence, saved vectors and reconstructed report margins. Immutable-run and tamper checks recompute report attribution and policy traces. Missing-evidence fixtures expose inputs and annotations without invented predictions; HTTP exports keep report references outside interpreter inputs and link the formatted guide to its recorded report.

The actual run fits the new packet classifier on 186 training packets and the report classifier on 210 training reports, plus the previous 96-packet bridge. It scores 108 development packets and 124 reports. The tracked report matches saved evidence and independently recomputed regressions against both matched packet ML and the bridge. All 124 report vectors, 248 report margins, 216 packet vectors and 864 packet margins verify. Nine dataset validators pass; earlier recorded sources, data, predictions and scores remain unchanged. No Jev calls were made.

Browser review covered every inference path, both report score fields, report selection, current/stale conflict pairs, policy traces, reference reveal and training inputs without evaluation predictions. Revealing references preserves an expanded policy explanation. Copy feedback appeared and downloaded JSON matched the selected input and report vectors. The formatted guide linked to its recorded report and returned to the same packet, arm and step. Desktop, 820-pixel and 390-pixel layouts showed no page overflow; browser error logs were empty. The earlier structured comparison retained its scores.

These checks establish evidence integrity and app behavior. The annotations, validity threshold and comparable-report grouping remain drafts. Explicit report expressions cover the pack's written vocabulary; their perfect development score does not establish blind transfer or operational accuracy.


## Matched report-language and Jev checks

Twenty new tests cover matched wording and separate annotations, clause meanings, reference-fed policy diagnostics, train-only vocabularies, immutable local evidence, fitted contributions and field regressions. Hosted fixtures check the exact 296-request plan, text-only report boundaries, incomplete aggregation, malformed probability rejection, credential redaction and stop conditions. Missing or failed responses remain in planned denominators. Read-only service and HTTP checks expose missing results, export exact inputs, reject foreign origins and preserve reader context. Replay tests preserve four exact bodies across three repeats, separate agreement from correctness and verify saved evidence before display.

The actual local study scores 140 packets and 156 reports. Both fitted report arms preserve 312 report vectors and 624 score margins; the frozen packet bridge preserves 140 vectors and 560 margins. The hosted comparison completed 296 calls, and the diagnostic replay completed another 12, all without reported failures. Their prepared protocols, source/data hashes, exact requests, normalized responses, policy traces, tracked checkpoints and recomputed scores verify. All ten data validators pass. Historical inference sources, nine original data files, 67 evidence files and 18 recorded results remain unchanged; the historical source audit identifies only the five previously changed app/reader/walkthrough files.

Browser review covered actual matched training wording without evaluation predictions, report selection, both report score fields, the frozen packet classifier, direct Jev and report/policy Jev. Reference reveal preserves expanded policy traces and marks wrong report meanings as well as packet decisions. Copy feedback appeared; downloaded training input matched the prepared bundle, and downloaded Jev input matched its actual saved request. The formatted guide returns to the same packet, arm and report. The replay table shows repeated meanings separately from original predictions. Desktop, 820-pixel and 390-pixel layouts keep tables inside scrollable containers. The final Python suite passes all 162 tests; all nine JavaScript tests and browser-script syntax checks pass. Browser error logs are empty. These checks establish evidence integrity and app behavior, not valid operational references or representative network performance.

## Measured-function comparison and inspection

The 68-packet/88-report pack validates, including 34 single-field pairs, fresh families, separate annotations and two policy gaps declared before inference. Both raw runs verify against frozen commit `2f65910`; the 176 hosted requests all completed. Verification recomputes report scores, packet traces, regressions and failure-inclusive denominators. All 176 saved ML report vectors and 352 fitted margins verify. The tracked checkpoints match raw evidence. Earlier inference sources, data and recorded results remain unchanged.

The new workbench preserves exact question differences, report selection, fitted ML margins, returned Jev distributions and a separately revealed reference-policy diagnostic. Its downloaded Jev input matches the saved request. Missing or invalid runs remain unavailable rather than acquiring fabricated predictions; local-origin protection covers the new endpoints. The formatted guide returns to the same packet, interpreter and report. Phone, tablet and desktop checks keep tables in scrollable containers. The full suite passes 172 Python tests; focused service checks also pass after the final diagnostic-display change. All nine JavaScript tests and six syntax checks pass. These checks verify implementation and evidence, not reference validity or operational readiness.

## Instrument metadata policy checks

Eleven new tests cover reproducible fresh families, prewritten independent references, malformed and unresolved scope, stale/unlinked exclusion, deduplicated exact requests, identical readings across policies, recording before calls, credential redaction, rate-limit and malformed-response stops, shared-response failure denominators, fitted ML margins and guarded read-only exports. A fresh data-only fixture exposes requests and references without inventing predictions.

All 32 Jev calls completed without failures. Both raw runs and tracked checkpoints verify against frozen preparation source `9904290`. Sixteen distinct texts join 96 correlated report occurrences; each reader’s predictions remain identical across its two policy arms. The 32 local ML vectors and 64 fitted margins reconstruct. Earlier development evidence and historical data, evidence and scored results remain unchanged.

Browser review covered matched grouping switches, identical request downloads, same-function conflicts, missing and ambiguous scope, stale exclusions, unlinked-report diagnostics, draft-reference reveal, fitted ML contributions, guide navigation and return context. Layouts at 390, 820 and 1280 pixels keep tables inside their containers; browser error logs are empty. These checks establish recording, comparison and interface behavior. They do not settle the domain definition, validate the draft references or establish operational metadata trust.

The [inspection audit](../checkpoints/metadata-policy-inspection-2026-10-02.json) records the verified counts and comparison boundaries.

## Declared-domain checks

Nine new tests cover reproducible fresh families and separate references, the exact domain-only question difference, no structured metadata or reference leakage into Jev, safe declaration decoding, unchanged operation readings in software controls, no invented domain probabilities, recording before calls, credential redaction, shared failures, immutable runs, fitted margins and guarded inspection/export routes. Data-only fixtures keep missing predictions explicit.

All 60 Jev calls succeeded from frozen preparation commit `0d5c214`. Exact requests, normalized responses, occurrence joins, domain overrides, policy predictions, tracked checkpoints and scores verify. Thirty distinct texts supply 128 correlated occurrences. Sixty ML vectors and 120 fitted score margins reconstruct from the frozen 210-report recipes. All earlier development evidence and historical data, evidence and scored results remain unchanged.

Browser review covered the missing-declaration question difference, same-request software switches, exact hosted and local downloads, hidden and revealed references, ambiguous declarations, stale and disconnected faults, comparable normal/fault conflicts, unchanged ML margins, guide links and restored source/report context. Layouts at 390, 820 and 1280 pixels contain their tables; browser error logs are empty. These checks establish comparison and interface behavior, not the authority of instrument declarations, specialist approval or operational readiness.

The [inspection audit](../checkpoints/declared-domain-inspection-2026-10-02.json) records verified counts and boundaries.

## Declaration consistency verification, October 2

All 203 Python tests, 14 dataset validators, nine JavaScript tests and nine browser-script syntax checks pass. New checks cover explicit enum parsing, occurrence-specific domains, shared failures, independent references, ineligible-report exclusions, fitted margins, immutable evidence and corrected raw-versus-software attribution. Prior data, evidence and recorded results verify unchanged.

The live study records 40 Jev requests without failures, 40 distinct texts and 160 correlated occurrences. Its local evidence includes 80 actual report vectors and 160 reconstructed fitted margins. Exact browser downloads match saved Jev requests for both policies. Browser checks at 390, 820 and 1280 pixels show no page overflow or console errors; guide returns restore the case and policy. See the [inspection audit](../checkpoints/declaration-trust-inspection-2026-10-02.json).


## Task-fit interpretation and coverage

At preparation, the pack validator confirmed 88 reports in 44 split-disjoint families, including 24 sealed evaluation reports. Six inference tests check matched facts and isolated changes, exclusion of poisoned answer fields, preregistered call counts, repeat request hashes, strict probability validation, missing-response denominators, hidden reading errors, unknown-review retention and checksum tampering. Three service/diagnostic tests check explicit missing-run behavior, inaccessible evaluation routes, guide return paths and the distinction between accepted readings and domain recommendations. The routing diagnostic leaves response files unchanged.

The 96 development, 72 repeated and 24 calibration calls verify against their saved sources, data and requests. The Structured candidate freeze verifies. The read-only workbench exposes complete actual inputs and replies, independently revealed draft references, software traces and frozen local fitted evidence. At that checkpoint, final evaluation inputs, labels, identifiers and requests were excluded from catalog and case routes. The later advisory evaluation below records the conditions for opening completed cases. UI inspection makes no hosted calls.

Browser review covered the Prose timing-recovery error hidden by correct routing, the corrected Structured reading, the calibration regulator error, probability sweeps at 0.60 and 0.90, paired-report navigation, browser Back and the formatted guide's return link. Section navigation preserves revealed references. Phone, tablet and desktop checks at 390, 820 and 1280 pixels showed no page overflow; wide tables scroll within their containers. Browser error and warning logs were empty. The final suite passes all 212 Python tests, all 14 study validators plus the historical dataset validator, nine JavaScript tests, ten script syntax checks and launcher syntax.

These checks establish evidence integrity and inspection behavior. They do not establish a safe routing threshold, independent references, representative network reports or operational calibration. The historical release bundle excludes task-fit raw evidence; a fresh clone shows missing predictions explicitly.


## Analyst-facing held-out evaluation

The user selected analyst-facing recommendations. Preparation commit `3f3c8b8` records the 0.60 advisory display threshold, author-set synthetic research criteria, candidate/calibration fingerprints and new wrapper source before any evaluation call. Three new tests cover calibration-only boundary selection, threshold tampering, immutable freezes, confident unknown and low-confidence withholding, mandatory analyst review, preregistration before calls, rate-limit stop behavior, key redaction and rerun refusal.

All 24 actual evaluation calls completed and verify. Replay reproduces both full scores and the advisory assessment: 21/24 report readings, 22/24 packet decisions, 17 qualifying readings, nine domain suggestions and one wrong qualifying core suggestion. The two zero-error research criteria fail. The interface displays that failure and retains analyst review on all 24 reports.

A further service fixture keeps evaluation unavailable without a complete verified assessment, opens it when all required evidence matches, rejects nonfrozen evaluation arms and reseals cases after an assessment count changes. Fresh clones without raw runs retain explicit missing results. These controls preserve the one-shot comparison and do not validate the research criteria as operational limits.

Final browser review covered the failed criterion table, the direct link to the 0.84 wrong suggestion, withholding its 0.57 paired reading, browser Back, guide return links and the analyst review plan. Desktop, tablet and phone checks at 1280, 820 and 390 pixels showed no page overflow; tables remain scrollable within their containers. Browser error and warning logs were empty. The full suite passes 216 Python tests; focused service tests, nine JavaScript tests and all ten syntax checks also pass. Historical and 14 study validators pass, and all five task-fit runs verify unchanged.

A final navigation check found that initially hidden evaluation results could miss their URL anchor before evidence loaded. The workbench now restores the requested section after rendering and adds a held-out-result link once verified evidence is available. Browser inspection confirms the evaluation panel lands at the top of the viewport; the advisory protocol returns to that same section.

## Public-data preflight, October 3

The assessment selectively extracts OpenRCA query/reference files and one middleware metric file with ZIP CRC checks, then records their hashes and observed schemas. RCAEval preparation downloads three pinned RE2 Online Boutique cases, verifies publisher hashes, and checks the local files against their recorded fingerprints. Metric window sizes and log/trace row counts match the published case index. The checkpoint records source hashes and separate prepared-input/reference fingerprints. Raw files stay outside Git.

Six new tests reject answer-bearing columns, changed source files, duplicate or foreign manifest paths, invalid timestamp scales and empty windows. They preserve missing values and ensure incident samples cannot change the baseline scale. The actual three-case preparation verifies the Parquet schemas and writes inputs separately from references; a leakage scan finds no source directories or answer metadata in the states.

All 222 Python tests, nine JavaScript tests, 15 dataset validators, ten browser-script syntax checks and launcher syntax pass. The live formatted assessment and its Markdown download serve correctly. These checks validate access, input preparation and historical preservation; no public-data model scores or operational claims are recorded.
