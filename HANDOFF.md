# Handoff: Jev incident triage experiments

## Purpose and current state

I compare hosted Jev, trained ML and rules on incident decisions for the fictional **Northstar Telecom** network. The study examines failures and whether clearer inputs, questions or software calculations improve decisions. It recommends diagnostics without executing network changes.

Two experiments are complete. The app includes an eight-chapter study walkthrough, saved-case inspection, an ML feature microscope, a local evidence sandbox and a formatted study reader at `/study`. The reader uses the repository Markdown and preserves the selected walkthrough context. Experiment 3 adds development studies of input facts, questions, evidence selection, ML features and report interpretation. The latest `/report-language` workbench compares matched ML training phrases with direct-versus-report Jev triage on 140 further packets, then exposes an exact-request diagnostic replay. Both workbenches show actual inputs, responses and fitted explanations where available. References need specialist review and no final held-out set exists.

The historical handoff and evidence belong to the [`study-evidence-v1` release](https://github.com/mumit/Jev-incident-triage-experiments/releases/tag/study-evidence-v1). Its tag identifies the source version; the bundle manifest records the full source commit. The frozen inference checkpoint is `6a44f62`. Later UI and documentation work preserves its four inference files.

## Read first

1. [AGENTS.md](AGENTS.md): project conventions and experimental controls.
2. [README](README.md): installation, startup and checks.
3. [Experiment overview](docs/experiment-overview.md): data definitions, both experiments, actual Jev input changes and interpretation.
4. [Measured review](docs/performance-review.md): scores, regressions, individual cases and fingerprints.
5. [Run bundle](docs/run-bundle.md): download, verification and restoration.
6. [Walkthrough guide](docs/observatory.md): inspecting requests, responses, local scores and paired changes.

## What the results support

All-four test accuracy was 90.9% for rules, 59.5% for original ML, 96.8% for revised ML, 57.7% for original Jev and 90.9% for focused Jev. Focused Jev's 100% validation accuracy did not carry over to test. Dependency changes remain difficult, and high-probability errors occur.

Priority explains much of the improvement. The separate software-priority score replaces priority with the policy calculation while retaining the three model decisions. It does not change saved predictions. Several input and feature changes happened together, so the results do not isolate their individual effects.

The scenarios are constructed teaching examples, with correlated variations within families. They do not establish operational accuracy, scenario realism, calibrated probabilities or restoration-time savings. Five test packets and four challenge packets had appeared in earlier runs; subsequent review exposed their failures. Future improvements need new development and evaluation families.

## Historical evidence and setup

The repository contains synthetic inputs, separate answer keys, code and measured reports. The release bundle adds the four documented runs and freeze record under ignored `runs/`. Without it, data inspection and local ML replay work, but historical comparisons and request-hash checks are unavailable.

Follow the [restore instructions](docs/run-bundle.md), then start the app and open `/explorer` on your server. Port 8766 is the default. Existing case links use the original working session at port 8768; substitute your own port. Restoring and inspecting the bundle requires no Jev calls. New hosted comparisons require your own key in **Model settings** and incur provider charges.

## Comparison baseline

The [October 1 stocktake](docs/current-state.md) and `checkpoints/study-baseline-2026-10-01.json` record application and audit source `84e414a`, the frozen dataset, recorded settings and results. Verification checks source, data and portable historical evidence fingerprints and recomputes the saved scores. The comparison command reports deltas only for matching evaluation inputs, answer keys and policy. New families need a new baseline and changed variants on the same evaluation set.

## Experiment 3 development

Read the [development guide](docs/experiment-3-development.md) and its machine-readable report. The new pack has 72 training and 36 development packets across disjoint families. Four local classifiers share a recipe and differ only in textual input facts. They fit only the new training split. Rules remain unchanged.

All-four development accuracy is 16.7% for the compact baseline, 30.6% with dependency facts, 13.9% with measurement facts and 27.8% with both. Rules score 50.0%. These are small-sample draft-reference results on different data, not deltas from experiment 2. Raw pilot predictions remain ignored; a fresh clone can replay them with the CLI or app button.

Jev completed all 144 requests with zero failures. All-four accuracy is 44.4% for the baseline, 41.7% with dependency facts, 38.9% with measurement facts and 41.7% with both. No variant gets both packets right in any of the 14 decision-changing pairs. The added facts fix no fully correct-packet errors and introduce one or two regressions. These results do not support adopting either addition.

Read the [reference review](docs/experiment-3-reference-review.md) before interpreting disagreements as model failures. The user selected NOC retention until current evidence links a fault to affected service as a synthetic teaching rule. Specialist review of the references and thresholds remains pending.

The [question-precedence comparison](docs/experiment-3-question-precedence.md) completed 32 calls on 16 new development packets. Explicit instructions score 93.8% against 56.3% for original questions on identical combined states. Six packets improve, but one stale-conflict failure remains with an owner regression.

The [conflict repetition](docs/experiment-3-conflict-repetition.md) then completed 48 calls on eight further packets in four pairs, repeated three times with both question sets frozen. Original questions score 0.0% in each repeat; explicit precedence scores 50.0%. Neither arm gets a full pair right. Explicit precedence gets every current-conflict packet right, but retains NOC on every stale-conflict packet in every repeat, regressing their originally correct domain owners. Its four decisions remain identical on all eight packets; original decisions vary on two load-panel packets. These are targeted development results, not deltas from the previous pack.

The [evidence-selection comparison](docs/experiment-3-evidence-selection.md) completed 36 calls on 12 new packets in six pairs. It freezes explicit questions and varies only input construction. Combined facts and added eligibility facts each score 75.0%; eligible observations only scores 100.0%. Selection fixes all three stale-conflict B packets and retains nine correct controls, with no newly wrong fields. Eligibility facts partly improve fields but fix no complete packet. The calculator uses freshness and visible paths, not malfunction classification or references. Raw reports remain inspectable and retained rows preserve source indices.

The [selection-robustness check](docs/experiment-3-selection-robustness.md) completed 48 calls on eight new packets, repeating both frozen inputs three times. Selected observations match all eight draft references in every repeat; combined facts match seven. Selection fixes one validity-boundary packet, repeated three times, and introduces no new wrong fields. Both inputs pass the partial-inventory, missing-inventory and multiple-domain controls and keep identical decisions across repeats. The multiple-domain reference remains provisional; agreement does not establish correctness or operational reliability.

The [structured ML comparison](docs/experiment-3-structured-ml.md) fits four matched classifiers on 96 new training packets and scores 64 development packets. Both feature blocks together match 52/64 draft references versus 24/64 for the text baseline, with 20/32 versus 6/32 pairs correct. It fixes 28 complete packets and loses none, but introduces eight wrong owner fields and ten wrong diagnostic fields on already-failed packets. Current transport faults still receive NOC at about 85% probability. Jev makes no calls in this comparison.

The [training-wording comparison](docs/experiment-3-wording.md) is complete on 80 new development packets. Counterbalancing “tests” and “diagnostics” weakens their method-word weights but scores 61/80 against 64/80 for matched coupled wording. It fixes one packet and loses four, with new owner, diagnostic and evidence errors. The original training bridge scores 65/80. The original combined candidate stays unchanged.

The [report-policy study](docs/experiment-3-interpretation.md) compares a text-only report classifier and explicit report rules feeding the same fixed policy. Separate report annotations describe domain and fault/normal/unknown meaning, independent of packet decisions. On 108 new development packets, Report ML scores 62/108 against 55/108 for matched packet ML and 70/108 for the previous frozen candidate. Report rules match all draft references on this simple authored pack. Inspect the report readings, policy traces and fitted contributions at **Comparison → Report interpretation and policy**. No Jev calls were made.

Experiment 3 reports are tracked under `checkpoints/`; exact requests, responses and fitted evidence stay in ignored `runs/experiment-3*/` and `runs/report-language*/` directories. The historical public bundle does not contain these later studies. A fresh clone shows missing predictions explicitly and can replay local ML without Jev. New hosted runs require a key and incur charges.

Raw KPI time-series anomaly detection remains separate. The historical dataset has narrative observations, not raw KPI time series.

## Working with Codex

Open the cloned repository as a Codex project so it reads `AGENTS.md`. A useful first task is:

> Read HANDOFF.md and docs/report-language.md. Verify saved local and Jev runs when available, then inspect the core acceptance-versus-refusal regression and the separate report annotations. Preserve every recorded inference source, data pack, request, reference and result. The broader ML wording result is negative; do not replace the original model or tune this inspected pack. Keep the teaching rule that current evidence must link a fault to affected service. The user selected normal handler reading on October 2: acceptance is normal for the measured handler, with completion assessed separately. Clarify only the reading instruction in a matched new-family comparison. Version any reference changes separately. Specialist review and new held-out families remain pending.

API keys, `.env`, local environments and run files stay out of Git. Preserve input/answer-key separation and report missing results explicitly. The ML microscope explains a fitted score, not physical causation; Jev's hosted weights and internal reasoning remain unavailable.

## Latest report-language study

The [report-language comparison](docs/report-language.md) uses 186 matched training packets, 210 annotations and 140 new development packets. Broader phrases score 86/140 against 90/140 for original report phrases: four fixes and eight regressions. On the same pack, Jev report interpretation feeding fixed policy scores 139/140 against 127/140 for frozen direct triage, fixing 13 packets and losing one. Jev misreads five core acceptance reports, four hidden by correct triage. These are draft-reference development results. The user subsequently selected acceptance as normal for the measured handler, with completion assessed separately.

Local evidence is `runs/report-language/development-2026-10-02-v1/`; hosted evidence is `runs/report-language-jev/development-2026-10-02-v1/`. The preparation, local and hosted checkpoints live under `checkpoints/report-language-*`. Frozen inference source is `c9c04b9`; subsequent commits add inspection and documentation. The historical public bundle contains neither later run. Missing raw evidence remains explicit in a fresh clone.


The exact-request [diagnostic replay](docs/report-language.md#repeatability-check-and-the-next-decision) completed 12 calls: two inspected acceptance texts and two refusal controls, each repeated three times. One acceptance text varies unknown/normal/unknown; the other stays unknown. Both refusal controls stay fault. Source is `d190f34`; raw evidence is `runs/report-language-replay/diagnostic-2026-10-02-v1/`, and its separate protocol/result checkpoints remain under `checkpoints/`. Preserve `report_language_repeat.py`. These repeated report responses do not update the original packet score.

The user resolved the [reference decision](docs/report-language-review.md) as **normal handler reading**. The next matched question study will keep report texts, choice criteria, domain questions, model and policy fixed while clarifying the reading instruction. Clarify expected rejection versus malfunction-driven refusal in either definition. Version future questions and references separately; keep all existing evidence intact.

## Measured-function trial preparation

The user selected successful acceptance as normal for the focal handler, with completion measured separately. [The measured-function protocol](docs/report-scope.md) prepares 68 new packets, 88 reports and 34 pairs. Both Jev arms receive identical texts and differ only in reading instructions. Frozen report ML recipes and rules provide controls. Two predeclared packets expose a separate function-comparability gap in the unchanged policy. Preserve this gap and separate report from triage correctness. Inference has not run. Use `scripts.run_report_scope` to validate, preflight, run and verify immutable evidence; earlier data and results stay frozen.
