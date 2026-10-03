# Historical study run bundle

The [`study-evidence-v1` release](https://github.com/mumit/Jev-incident-triage-experiments/releases/tag/study-evidence-v1) carries the recorded evidence for both completed experiments. The archive is a release asset; `runs/` remains ignored by Git.

## Contents

| Recorded run | Identifier |
|---|---|
| Experiment 1 validation | `718d977d25aa4634` |
| Experiment 2 validation | `c3519f8c7ec84814` |
| Experiment 2 test | `3739acf583a64c79` |
| Experiment 2 paired challenge | `908dac657e6740af` |

The archive contains each run's inputs, separate answer keys, predictions, metrics, metadata and job record, plus `runs/performance-freeze.json`. Successful Jev rows retain their recorded provider responses. The first validation run retains its five probability-format failures; experiment 2 has no failed or missing responses.

`bundle-manifest.json` records the source commit, inference checkpoint, Jev checkpoint, dataset fingerprints, file sizes and SHA-256 checksums. `RESTORE.md` repeats these instructions. Personal absolute paths in `input_file` metadata become repository-relative paths. JSON metadata formatting is normalized; prediction rows, returned probabilities and responses remain unchanged.

The archive contains only the four selected synthetic runs. It excludes the later task-fit development, repeat, calibration and held-out advisory evaluation runs, whose summaries are tracked under `checkpoints/task-fit-*`. Their exact requests and replies remain in ignored `runs/task-fit/`; a fresh clone without them shows missing predictions explicitly. It excludes credentials, `.env`, configuration files, local environments and unrelated runs. Creation checks credential fields, known local keys, token patterns, personal paths and excluded operator identities. The bundle has no model weights.

## Download and restore

Use a fresh clone to avoid conflicts with existing local evidence. The commands below use GitHub CLI; the same files can be downloaded from the release page.

```bash
git clone https://github.com/mumit/Jev-incident-triage-experiments.git
cd Jev-incident-triage-experiments
git switch --detach study-evidence-v1
uv sync --locked
mkdir -p runs/bundles
gh release download study-evidence-v1 --repo mumit/Jev-incident-triage-experiments --dir runs/bundles --pattern 'northstar-study-evidence-v1.zip*'
```

Check the downloaded archive checksum:

```bash
(cd runs/bundles && shasum -a 256 -c northstar-study-evidence-v1.zip.sha256)
```

Then verify and restore it:

```bash
uv run --locked python -m scripts.study_bundle verify runs/bundles/northstar-study-evidence-v1.zip
uv run --locked python -m scripts.study_bundle restore runs/bundles/northstar-study-evidence-v1.zip
uv run --locked python -m triage_bench.app --port 8766
```

Open [the walkthrough](http://127.0.0.1:8766/explorer). Restart an already-running app after restoring, so it loads the historical runs.

Verification checks every file, frozen dataset and inference source before restoration. Restore accepts existing identical files and refuses to overwrite different evidence or write through symlinks. It writes only the selected `runs/` paths. A changed inference checkout will fail verification; use the release tag to inspect the recorded experiment first.

To continue development, create a branch from the release checkout. Keep the original runs intact and store new comparisons under new IDs. Restoring or inspecting evidence makes no hosted API calls. Enter your own Jev key only when running new hosted comparisons.

## Check the restored study

Run the checks listed in the [README](../README.md#checks). With the bundle restored, the historical-request and provider-export checks run rather than skip. Rebuild the measured report with your own server URL if needed:

```bash
uv run --locked python -m scripts.review_performance --base-url http://127.0.0.1:8766
```

Changing the server URL changes only the report's local links. The script reads recorded scores without fitting models or calling Jev. [The handoff](../HANDOFF.md) explains the next experiment and the limits of this evidence.

## Build a new bundle version

Commit the matching source and documentation first, then create the archive outside the tracked tree or under ignored `runs/`:

```bash
uv run --locked python -m scripts.study_bundle create runs/bundles/northstar-study-evidence-v1.zip
```

The builder requires a clean working tree and refuses to overwrite an archive. This version packages only the four fixed study runs. A future experiment needs an updated run selection, manifest version, release tag and documentation; do not replace the v1 asset with different results.

## Subsequent development evidence

The v1 historical archive does not contain the experiment 3 input-facts or question-precedence runs. Their reports are tracked under `checkpoints/`; exact requests and responses remain in ignored local run directories. A fresh clone can inspect the separate draft packs and prepared requests, and replay local ML for the input-facts pack. Missing hosted predictions stay explicit. New hosted runs require a key and incur provider charges; they may produce different responses.

The repeated conflict run is also outside the v1 archive. Its tracked report records the master plan and three repetitions; raw files remain in ignored `runs/experiment-3-conflicts/`. A fresh clone can inspect the new draft pack and prepared requests, but needs saved run files to inspect returned decisions.

The subsequent evidence-selection run is also excluded from the historical release. Its tracked report is `checkpoints/experiment-3-selection-2026-10-02.json`; raw requests and responses remain in ignored `runs/experiment-3-selection/`. A clone can inspect prepared inputs and the report, but needs those run files to display actual per-packet responses. [The selection guide](experiment-3-evidence-selection.md) documents reproduction.

The selection-robustness run is also excluded from the historical release. Its tracked report is `checkpoints/experiment-3-robustness-2026-10-02.json`; exact repeated requests and responses remain in ignored `runs/experiment-3-robustness/`. A clone exposes missing responses explicitly. [The robustness guide](experiment-3-selection-robustness.md) records reproduction and limitations.

The structured ML comparison is also outside the historical release. Its report is checkpoints/experiment-3-structured-ml-2026-10-02.json; exact inputs, predictions, vectors and explanations live in ignored runs/experiment-3-structured-ml/. A clone can inspect prepared features and run the local comparison without a Jev key. [The feature guide](experiment-3-structured-ml.md) records reproduction. Do not replace the historical release asset with these results.

The [training-wording comparison](experiment-3-wording.md) also keeps its report and draft data in Git, with exact fitted evidence under ignored `runs/experiment-3-wording/`. It is absent from the historical release. The local CLI can replay it without hosted calls; a clone without raw evidence reports missing predictions explicitly.

The [report-policy study](experiment-3-interpretation.md) tracks its new packet data, separate report annotations and result checkpoint. Exact predictions, policy traces, vectors and score margins remain in ignored `runs/experiment-3-interpretation/` and are absent from the historical release. Replay with `python -m scripts.run_experiment3_interpretation run --output runs/experiment-3-interpretation/my-report-study`, then verify that directory with the same CLI. Without saved evidence, the app exposes inputs and annotations and reports missing predictions explicitly. Replay needs no Jev key.


The [report-language study](report-language.md) and its diagnostic replay are also outside the historical release. Tracked checkpoints preserve preparation and result fingerprints. Raw local fits, hosted requests/responses and repeated requests remain in ignored `runs/report-language/`, `runs/report-language-jev/` and `runs/report-language-replay/`. The `/report-language` workbench exposes missing predictions explicitly. Local ML can be replayed without a key; repeating hosted inference makes new charged calls and does not recover the original responses. The exact-request diagnostic replay requires its original saved hosted evidence. Preserve the published v1 asset unchanged.

The [measured-function trial](report-scope.md) also remains outside the historical release. Its tracked pack and checkpoints live in Git; raw local and hosted evidence stays in ignored `runs/report-scope/` and `runs/report-scope-jev/`. Preserve those directories separately to share the original responses and fitted explanations. A fresh clone can rerun local controls; new hosted inference incurs charges and produces new evidence.

## October 2 instrument metadata comparison

The [metadata policy study](metadata-policy.md) holds each interpreter’s readings fixed across asset and metadata grouping on 48 new development packets. Both Jev question controls improve 26/48 → 40/48, fixing 14 packets without losses. Frozen original and broader ML stay at 24/48; report rules improve 24/48 → 30/48. Sixteen distinct report texts supply 96 correlated occurrences; only 32 Jev calls were made. Metadata enters policy alone, with conservative handling of unresolved relevant scope.

Inspect **Comparison → Instrument metadata policy** at `/metadata-policy` for raw scope, both policy traces, exact requests, returned meanings and ML score contributions. References remain drafts. The [recorded domain choice](metadata-domain-review.md) identifies the declared instrument source, with service relevance checked separately by policy. These later raw runs are outside the historical public bundle.

## October 2 declared-domain comparison

The completed [declared-domain study](declared-domain.md) records source preparation `0d5c214` and tracked protocol/local/hosted checkpoints. Its raw evidence remains in ignored `runs/declared-domain/development-2026-10-02-v1/` and `runs/declared-domain-jev/development-2026-10-02-v1/`, outside the historical public release. A fresh clone can replay frozen local controls and inspect inputs; saved responses and fitted evidence require the corresponding later runs. Do not replace the historical bundle with these results.

The [recorded trust choice](declaration-trust-review.md) retains NOC until conflicting declarations are resolved. The [matched guard study](declaration-trust.md) records that comparison. Specialist review and held-out evaluation remain pending.

## October 2 declaration consistency comparison

The [declaration guard study](declaration-trust.md) records preparation `ee12a91`. Its raw runs live in ignored `runs/declaration-trust/development-2026-10-02-v1/` and `runs/declaration-trust-jev/development-2026-10-02-v1/`, outside the historical release. Tracked evaluation checkpoints correct a generic attribution error without altering those files; packet and distinct-text scores were unaffected. A later evidence bundle must include these raw runs and the separate evaluator at its recorded version.
