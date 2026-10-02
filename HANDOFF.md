# Handoff: Jev incident triage experiments

## Purpose and current state

I compare hosted Jev, trained ML and rules on incident decisions for the fictional **Northstar Telecom** network. The study examines failures and whether clearer inputs, questions or software calculations improve decisions. It recommends diagnostics without executing network changes.

Two experiments are complete. The app includes an eight-chapter study walkthrough, saved-case inspection, an ML feature microscope, a local evidence sandbox and a formatted study reader at `/study`. The reader uses the repository Markdown and preserves the selected walkthrough context. Experiment 3 now has a separate draft training/development pack, deterministic dependency and measurement-age facts, prepared Jev requests and a matched local ML pilot at `/experiment-3`. Jev has not run on the new pack, references need specialist review and no final held-out set exists.

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

The next task is to review dependency semantics, telemetry validity and diagnostic alternatives with a network specialist. Then prepare a bounded hosted Jev comparison on the same four inputs, and a separate ML comparison of structured dependency/age features. New revisions need further development cases. Freeze reviewed references, transformations and questions before generating final held-out families.

Raw KPI time-series anomaly detection remains separate. The historical dataset has narrative observations, not raw KPI time series.

## Working with Codex

Open the cloned repository as a Codex project so it reads `AGENTS.md`. A useful first task is:

> Read HANDOFF.md and docs/experiment-3-development.md. Verify the draft pack and replay the local pilot. Inspect the controlled pairs, exact prepared Jev inputs and ML regressions. Preserve historical inference, data and evidence. Document specialist-review questions and a bounded Jev development run plan before hosted inference.

API keys, `.env`, local environments and run files stay out of Git. Preserve input/answer-key separation and report missing results explicitly. The ML microscope explains a fitted score, not physical causation; Jev's hosted weights and internal reasoning remain unavailable.
