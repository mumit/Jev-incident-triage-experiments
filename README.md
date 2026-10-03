# Jev incident triage experiments

I compare Jev, trained machine learning (ML) and rules on incident decisions for **Northstar Telecom**, a fictional network. The lab exposes failures, compares changes to inputs and questions, and keeps measured results available for review.

The lab recommends diagnostics. It does not execute network changes. The data consists of constructed teaching scenarios; scores do not establish performance on a real network. Raw KPI time-series anomaly detection remains a separate future experiment.

## Start

Clone this repository and start the local app with Python 3.11+ and `uv`:

```bash
git clone git@github.com:mumit/Jev-incident-triage-experiments.git
cd Jev-incident-triage-experiments
uv sync --locked
uv run --locked python -m triage_bench.app --port 8766
```

Open [the comparison lab](http://127.0.0.1:8766/) or [the study walkthrough](http://127.0.0.1:8766/explorer). On a Mac, `start.command` starts the app at port 8766; its fallback installs the pinned requirements into a local virtual environment when `uv` is unavailable.

The current working session uses [port 8768](http://127.0.0.1:8768/explorer). Links to individual saved cases in the measured review use that session. Substitute your server's port when following those links.

Startup does not call Jev or download language-model weights. The app fits local classifiers when first needed and reuses them within the server session. Enter a key in **Model settings** to run new hosted Jev comparisons. Hosted calls incur provider charges. Keys entered there stay in server memory; `.env` is an optional ignored configuration file.

## Continue the work

Start with [HANDOFF.md](HANDOFF.md) for the current state, experimental controls and next task. Restore the four historical runs from the [study evidence release](https://github.com/mumit/Jev-incident-triage-experiments/releases/tag/study-evidence-v1) using the [bundle guide](docs/run-bundle.md). The archive stays outside Git history; `runs/` remains ignored.

The [October 1 baseline](docs/current-state.md) fixes the current source, data, settings and results before experiment 3. Its `checkpoints/study-baseline-2026-10-01.json` supports file verification and comparisons with future saved runs.

Experiment 3 now has a [development workbench](http://127.0.0.1:8768/experiment-3) with 72 new training packets, 36 development packets, deterministic input facts, matched local ML results and a completed 144-request Jev comparison. Its references remain provisional. Use `/experiment-3` on your own server. [The development guide](docs/experiment-3-development.md) records the controls, results and next review.

The [question-precedence comparison](docs/experiment-3-question-precedence.md) adds 16 new development packets and a matched two-arm Jev trial. Explicit precedence scores 93.8% against 56.3% for original questions on identical combined evidence. References remain drafts; one owner regression is visible. Choose **Comparison** in the workbench to switch studies.

The [conflict repetition](docs/experiment-3-conflict-repetition.md) checks four new pairs three times with the frozen question sets. All 48 requests completed. Explicit precedence repeats the same stale-conflict failure across all four families; the app exposes each repetition and packet-level agreement.

The [evidence-selection comparison](docs/experiment-3-evidence-selection.md) completed 36 calls on 12 further packets with fixed explicit questions. The combined baseline and eligibility summary each score 75.0%; eligible observations only scores 100.0%, retaining current-conflict and empty-evidence controls. These are small draft-reference results, not operational reliability.

The [selection-robustness check](docs/experiment-3-selection-robustness.md) completed 48 calls on eight new packets, repeating both frozen inputs three times. Selected observations match all eight draft references in every repeat; combined facts match seven. Selection fixes one validity-boundary packet, repeated three times, and introduces no new wrong fields. Both inputs pass the partial-inventory, missing-inventory and multiple-domain controls and keep identical decisions across repeats. The multiple-domain reference remains provisional; agreement does not establish correctness or operational reliability.

The [structured ML comparison](docs/experiment-3-structured-ml.md) fits four matched classifiers on 96 new training packets and scores 64 development packets. Both feature blocks together match 52/64 draft references versus 24/64 for the text baseline, with 20/32 versus 6/32 pairs correct. It fixes 28 complete packets and loses none, but introduces eight wrong owner fields and ten wrong diagnostic fields on already-failed packets. Current transport faults still receive NOC at about 85% probability. Jev makes no calls in this comparison.

The [training-wording comparison](docs/experiment-3-wording.md) is complete on 80 new development packets. Counterbalancing “tests” and “diagnostics” weakens their method-word weights but scores 61/80 against 64/80 for matched coupled wording. It fixes one packet and loses four, with new owner, diagnostic and evidence errors. The original training bridge scores 65/80. The original combined candidate stays unchanged.

The [report-policy study](docs/experiment-3-interpretation.md) compares a text-only report classifier and explicit report rules feeding the same fixed policy. Separate report annotations describe domain and fault/normal/unknown meaning, independent of packet decisions. On 108 new development packets, Report ML scores 62/108 against 55/108 for matched packet ML and 70/108 for the previous frozen candidate. Report rules match all draft references on this simple authored pack. Inspect the report readings, policy traces and fitted contributions at **Comparison → Report interpretation and policy**. No Jev calls were made.

## Read and explore

| Document | What it covers |
|---|---|
| [Experiment overview](docs/experiment-overview.md) | Purpose, data definitions, both experiments, input changes, results and the next experiment. |
| [Experiment 3 development](docs/experiment-3-development.md) | Draft cases, transformations, matched ML/Jev results and exact request inspection. |
| [Instrument metadata](docs/metadata-policy.md) | Fixed readings, matched policy grouping and remaining domain-definition decision. |
| [Measured-function reading](docs/report-scope.md) | Matched question change, report/triage results and hidden policy gaps. |
| [Report language and Jev](docs/report-language.md) | Matched training result, direct-versus-report Jev comparison and the selected handler reference. |
| [Report interpretation and policy](docs/experiment-3-interpretation.md) | Report annotations, interpreter errors, policy traces and matched architecture results. |
| [Training wording](docs/experiment-3-wording.md) | Matched method-word intervention, negative result, controls and regressions. |
| [Structured ML features](docs/experiment-3-structured-ml.md) | Matched feature sets, fitted vectors, score contributions and field regressions. |
| [Selection robustness](docs/experiment-3-selection-robustness.md) | Validity boundaries, inventory gaps, multiple-domain controls and three repeated fixed requests. |
| [Evidence selection](docs/experiment-3-evidence-selection.md) | Software eligibility, retained/removed observations, matched results and limitations. |
| [Conflict repetition](docs/experiment-3-conflict-repetition.md) | Repeated fixed questions, conflict recurrence and response variation. |
| [Question precedence](docs/experiment-3-question-precedence.md) | Exact instruction changes, new paired cases, results and the remaining regression. |
| [Experiment 3 reference review](docs/experiment-3-reference-review.md) | Unresolved assumptions, hosted run controls and reproduction. |
| [Walkthrough guide](docs/observatory.md) | The eight chapters, case inspection, ML microscope, Jev requests and local sandbox. |
| [Learning guide](docs/learning-guide.md) | Running comparisons and interpreting disagreements. |
| [Measured performance review](docs/performance-review.md) | Scores, saved case links, regressions, run IDs and fingerprints. |
| [Dataset card](docs/dataset-card.md) | Construction, family splits, paired challenges and realism limits. |
| [Policy](docs/policy.md) | The four decisions and fictional priority rules. |
| [Evaluation plan](docs/evaluation-plan.md) | Scoring, experimental controls and proposed future checks. |
| [Samples](docs/samples.md) | Input excerpts and separate reference decisions. |
| [Run bundle](docs/run-bundle.md) | Download, verify and restore historical study evidence. |
| [Verification](docs/verification.md) | Current tests, browser checks and publication limits. |

Choose **Read study** for the formatted experiment overview at `/study`, with section navigation, expandable tables, copyable code and links into case inspection. **Return to walkthrough** restores the selected packet, approach, field and chapter. **Download Markdown** keeps the source available for editors. The page reads the Markdown on each request.

In the walkthrough, start the guided tour with the radio scheduler validation case. Move through **Evidence**, **Decisions** and **Inside an approach**. **Paired change** compares controlled inputs. The sandbox changes a copy and runs only rules and the two local ML variants; it does not call Jev or change saved results.

## Approaches and experiments

Every approach selects an initial investigating team, priority, next diagnostic check and whether evidence is insufficient.

| Approach in the app | Implementation |
|---|---|
| Rules | Fixed keyword routing and the exact impact-priority calculation. |
| ML · original | Word TF-IDF features and four logistic regression classifiers. |
| ML · revised | Compact evidence, word/character features and structured impact. Its priority classifier uses impact features alone. |
| Jev · original | Hosted `jev-1.13.0`, the original state and short Choice definitions. |
| Jev · focused | The same checkpoint and policy, compact evidence and explicit Choice definitions. |

Experiment 1 evaluated the original approaches. Experiment 2 revised ML's features and Jev's state and questions after validation review, then froze them before full test and challenge checks. Both ML variants fit only the original 600 training records. Each ML/Jev pair receives the same state string; their training histories differ. The rules use observation text and structured impact.

**With software priority** is a separate score that replaces priority with the exact policy calculation while retaining the three model decisions. Saved predictions remain unchanged. Experiment 3 tests dependency coverage and measurement age separately on a new draft pack. Local ML and hosted Jev development comparisons are complete. Specialist review and final held-out evaluation remain pending.

## Data and saved results

The frozen dataset contains 600 training, 220 validation, 220 test and 24 challenge packets. Regular families contain 20 correlated variations; the challenge has 12 pairs across four types. The 11-packet learning set is a subset of validation. Training, validation and test families are disjoint. Five test and four challenge packets had appeared in earlier runs, so the full checks were not entirely untouched evaluations.

The repository contains the synthetic inputs, separate answer keys, source code and measured reports. Raw local runs and the freeze record remain in ignored `runs/`. A fresh clone can explore the data, fit local ML and use the sandbox, but cannot display historical predictions or verify their hashes without those run files. Missing results remain explicit. New comparisons populate the comparison lab; the walkthrough reads the fixed run IDs documented in the measured review.

Jev's hosted weights and reasoning are unavailable. The app exposes its requests and returned answers. ML contributions reconstruct the fitted classifier's score; they do not establish causes in a network. Neither model's probabilities have been calibrated for operations.

## Checks

Node.js is needed for the browser-script checks, not for running the Python app.

```bash
uv run --locked python -m triage_bench validate
uv run --locked python -m scripts.run_experiment3_local validate
uv run --locked python -m scripts.run_experiment3_questions validate
uv run --locked python -m scripts.run_experiment3_conflicts validate
uv run --locked python -m scripts.run_experiment3_selection validate
uv run --locked python -m scripts.run_experiment3_robustness validate
uv run --locked python -m scripts.run_experiment3_structured_ml validate
uv run --locked python -m scripts.run_experiment3_wording validate
uv run --locked python -m scripts.run_experiment3_interpretation validate
uv run --locked python -m scripts.run_report_language validate
uv run --locked python -m scripts.run_report_scope validate
uv run --locked python -m scripts.run_metadata_policy validate
uv run --locked python -m scripts.run_declared_domain validate
uv run --locked python -m unittest discover -s tests -v
node --test tests/explorer-ui.test.cjs
node --check triage_bench/web/app.js
node --check triage_bench/web/explorer.js
node --check triage_bench/web/study.js
node --check triage_bench/web/experiment3.js
node --check triage_bench/web/report-language.js
node --check triage_bench/web/report-scope.js
node --check triage_bench/web/metadata-policy.js
bash -n start.command
```

The working checkout passes 142 Python tests and nine JavaScript tests. Two Python checks depend on historical run files and skip on a fresh clone. See [verification](docs/verification.md) for their scope.

## References

- [TypeSafe quickstart](https://docs.typesafe.ai/introduction/quickstart)
- [Jev model information](https://docs.typesafe.ai/models)
- [Jev limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
- [Scikit-learn text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction)
- [Scikit-learn logistic regression](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression)

I adapted the source from an earlier local synthetic incident benchmark. This repository adds the trained ML comparison, focused Jev requests and interactive study walkthrough.

The [report-language comparison](docs/report-language.md) uses 186 matched training packets, 210 annotations and 140 new development packets. Broader phrases score 86/140 against 90/140 for original report phrases: four fixes and eight regressions. On the same pack, Jev report interpretation feeding fixed policy scores 139/140 against 127/140 for frozen direct triage, fixing 13 packets and losing one. Jev misreads five core acceptance reports, four hidden by correct triage. These are draft-reference development results. The user subsequently selected acceptance as normal for the measured handler, with completion assessed separately. Inspect actual training phrases, returned meanings, policy traces and saved score contributions at `/report-language` or **Comparison → Report language and Jev**.

The exact-request diagnostic replay records unknown/normal variability on one acceptance wording and recurring unknown on another; both refusal controls remain fault. [The reference decision brief](docs/report-language-review.md) records the user-selected normal handler reading for the next matched question study.

The [measured-function trial](docs/report-scope.md) prepares a matched reading-instruction comparison on 68 new packets and 88 reports. Successful intake is normal for the focal handler, with completion assessed separately. The frozen policy has two predeclared function-comparability gaps. All 176 Jev calls completed. Original versus measured-function questions score 82/88 versus 83/88 report readings and 67/68 versus 68/68 packets. Two report fixes and one loss leave both predeclared policy gaps hidden by wrong readings. No earlier reference or result changes.

Inspect the new comparison at `/report-scope` or **Comparison → Measured-function reading**. Exact instructions, returned meanings, policy traces and reference diagnostics remain separate. The user selected instrument metadata first for a separate matched policy comparison.

The [metadata-first policy comparison](docs/metadata-policy.md) prepares 48 further development packets. Each reader feeds identical predictions to original and function/context grouping; metadata stays outside report interpretation. Missing and ambiguous scope controls remain conservative. The 96 report occurrences contain 16 distinct texts, so the hosted plan has 32 calls. The 32-call Jev run is complete: asset versus metadata grouping scores 26/48 versus 40/48 for both frozen question controls, fixing 14 packets without losses. Fault/normal readings match all 16 distinct texts; five domain readings disagree with draft references. The next decision concerns declared instrument domain versus domain-specific technical evidence.

Inspect `/metadata-policy` or **Comparison → Instrument metadata policy**. The [domain decision brief](docs/metadata-domain-review.md) explains the next choice using an actual request and response. The earlier public release remains unchanged.

The user selected declared instrument domain. The [next matched comparison](docs/declared-domain.md) prepares 64 further development packets and 60 hosted requests, with a software-domain control that preserves each reader’s fault/normal prediction. Existing studies stay frozen.
