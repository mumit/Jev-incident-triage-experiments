# Handoff: Jev incident triage experiments

## Purpose and current state

I compare hosted Jev, trained ML and rules on incident decisions for the fictional **Northstar Telecom** network. The study examines failures and whether clearer inputs, questions or software calculations improve decisions. It recommends diagnostics without executing network changes.

Two experiments are complete. The app includes an eight-chapter study walkthrough, saved-case inspection, an ML feature microscope, a local evidence sandbox and a formatted study reader at `/study`. The reader uses the repository Markdown and preserves the selected walkthrough context. Experiment 3 now has a separate draft training/development pack, deterministic dependency and measurement-age facts, matched local ML results and a completed 144-request Jev comparison at `/experiment-3`. The page exposes exact requests, responses and probabilities. References need specialist review and no final held-out set exists.

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

The [training-wording comparison](docs/experiment-3-wording.md) is complete on 80 new development packets. Counterbalancing “tests” and “diagnostics” weakens their method-word weights but scores 61/80 against 64/80 for matched coupled wording. It fixes one packet and loses four, with new owner, diagnostic and evidence errors. The original training bridge scores 65/80. The next study will separate report interpretation from policy application using new development families; the original combined candidate stays unchanged. Specialist review remains necessary before final held-out evaluation.

Experiment 3 reports are tracked under `checkpoints/`; exact requests, responses and fitted evidence stay in ignored `runs/experiment-3*/` directories. The historical public bundle does not contain these later studies. A fresh clone shows missing predictions explicitly and can replay local ML without Jev. New hosted runs require a key and incur charges.

Raw KPI time-series anomaly detection remains separate. The historical dataset has narrative observations, not raw KPI time series.

## Working with Codex

Open the cloned repository as a Codex project so it reads `AGENTS.md`. A useful first task is:

> Read HANDOFF.md, docs/experiment-3-development.md and docs/experiment-3-reference-review.md. Verify the draft pack and inspect the recorded ML/Jev comparison, controlled pairs and regressions. Preserve historical inference, data and saved runs. Read docs/experiment-3-question-precedence.md and docs/experiment-3-conflict-repetition.md. Read docs/experiment-3-evidence-selection.md and inspect selection fixes, controls, index mappings and eligibility-only partial improvements. Preserve selection.py, selection_data.py and selection_trial.py with their recorded fingerprints. Read docs/experiment-3-selection-robustness.md and inspect the repeated boundary fix and inventory controls. Preserve robustness_data.py, robustness_inference.py and robustness_trial.py with their recorded fingerprints. Keep Jev and selection frozen. Read docs/experiment-3-structured-ml.md, inspect the fitted vectors, score margins and field regressions, and preserve structured_data.py, structured_features.py and structured_ml.py. Read docs/experiment-3-wording.md and preserve wording_data.py and wording_ml.py with their recorded fingerprints. Inspect the negative matched result, stable synonym errors and new power-owner regressions. The next study should separate supervised observation interpretation from fixed policy application on new families. Preserve the user-selected NOC teaching rule, but do not claim specialist review. Use further development cases before revising the candidate; preserve the completed structured-feature comparison and inspect wording transfer failures. Do not treat the existing development cases as held-out evaluation.

API keys, `.env`, local environments and run files stay out of Git. Preserve input/answer-key separation and report missing results explicitly. The ML microscope explains a fitted score, not physical causation; Jev's hosted weights and internal reasoning remain unavailable.
