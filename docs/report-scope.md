# Measured-function reading experiment

## Question and controls

The user selected **normal handler reading** on October 2, 2026: successful request acceptance establishes normal operation of the measured handler, while registration completion remains a separate measurement. This synthetic teaching decision preserves the earlier report references; it does not establish specialist review.

The next comparison tests whether an explicit reading instruction helps Jev distinguish success, malfunction and uncertainty **at the function named in a report**. Both arms receive identical new report texts, domain questions, choice criteria and the pinned `jev-1.13.0` model. Their returned meanings feed the same frozen policy. Only `questions.reading.instructions` changes.

The original instruction remains intact in both requests. The measured-function arm appends:

> Judge the operation of the specific function this report explicitly measures, not the health of the whole component or wider service. Verified successful request intake or handler operation is normal for that measured function even if later registration or end-to-end completion is unmeasured. If the report instead measures completion, request acceptance alone leaves completion unknown. Success of a different function does not cancel an explicit malfunction of the measured function. Keep expected behavior, explicit malfunction and uncertainty distinct.

This paragraph contains several related clarifications. The comparison can measure their combined effect, not attribute a change to any one sentence. The [protocol checkpoint](../checkpoints/report-scope-protocol-2026-10-02.json) retains both complete questions and their unchanged choice criteria.

Original-phrase ML, broader-phrase ML and report rules provide controls on the same packets. The ML models reuse the frozen 210-report training recipes and settings from the report-language study. New annotations do not enter fitting, vocabulary construction or tuning. These controls help distinguish a reading problem from a policy problem; they are not new ML candidates.

## New synthetic cases

The pack contains **68 packets, 88 reports, 17 new families and 34 pairs**, all for development. A family groups variations of one incident pattern; its two variants share report templates and use different synthetic service graphs. Each pair changes one declared input field. Some changes alter the reference decision; others alter report meaning while leaving triage unchanged.

Eight core families cover intake success versus queue malfunction, completed versus unmeasured registration, intake versus completion scope, expected credential rejection, partial batch failure, missing receipt evidence, comparable intake contradictions and different functions on the same component. Nine further families exercise success, uncertainty and current/stale contradictions in transport, RAN and power.

For example, the same evidence receives different report readings when its stated measurement changes:

| Stated measurement | Remaining report text | Prewritten reading |
|---|---|---|
| Request intake | The handler accepts requests; later registration completion is not observed by this instrument. | Normal |
| Registration completion | The handler accepts requests; later registration completion is not observed by this instrument. | Unknown |

Both packets retain NOC because neither report establishes a fault explaining the degraded service. Report correctness and triage correctness therefore need separate scores.

Expected rejection of invalid credentials, with valid credentials accepted as specified, is normal validation behavior. An internal fault rejecting valid credentials is a malfunction. Accepting only part of a batch because of an explicit internal malfunction remains a fault.

Report annotations and packet decisions were written separately before inference. Domain prefixes and explicit measurement descriptions make this a controlled teaching pack, not a representative sample of network telemetry. Shared templates limit independence. All references remain provisional; no final held-out set exists.

## Policy gap identified before inference

The unchanged policy groups readings by **domain and asset**. It cannot distinguish the functions measured on that asset.

Two predeclared packets combine a failed registration-completion worker with successful request intake. Those observations can both be true: successful intake does not contradict failed completion. Their draft references assign core investigation. Supplying both correct report meanings to the frozen policy instead produces NOC because it detects normal/fault conflict on the same asset.

The affected packets are `NSS-be3b5d951cb0-a` and `NSS-9c0e4405ab09-a`. Their partners replace intake success with successful completion under comparable conditions, creating an actual contradiction that retains NOC. The manifest records this gap before any model calls.

Reference-reading-fed policy is an **evaluation diagnostic**, not model performance or an accuracy ceiling. A wrong report reading could hide the policy gap and accidentally produce the expected triage decision. Results must distinguish wrong readings with correct triage from correct readings with wrong triage.

## Execution and evidence

The hosted plan contains **176 serial requests**, one per report and arm. Arm order alternates by report. Each request is saved before the first call; there are no warmup calls or automatic retries. Access, configuration, rate-limit, checkpoint and network errors stop execution immediately. Three consecutive malformed responses also stop the run. Failed or missing report replies invalidate a packet prediction and remain in the full denominators.

Preparation freezes packet, annotation, question and source fingerprints. Local runs retain report vectors, fitted score margins and policy traces. Hosted runs retain exact requests, returned meanings, distributions and timing. Jev exposes returned probabilities, not internal reasoning or fitted weights. Earlier runs and the historical release remain unchanged.

```sh
.venv/bin/python -m scripts.run_report_scope validate
.venv/bin/python -m scripts.run_report_scope preflight
.venv/bin/python -m scripts.run_report_scope local --output runs/report-scope/development-2026-10-02-v1
.venv/bin/python -m scripts.run_report_scope hosted --output runs/report-scope-jev/development-2026-10-02-v1
.venv/bin/python -m scripts.run_report_scope verify --output runs/report-scope/development-2026-10-02-v1
.venv/bin/python -m scripts.run_report_scope verify --output runs/report-scope-jev/development-2026-10-02-v1
```

Raw run directories stay ignored. A fresh clone can inspect the tracked pack and protocol; missing predictions must remain explicit. New hosted runs require a server-side key and incur charges.

## Results and follow-up

Inference has not run on this pack. The first review will compare report fixes and losses, newly wrong individual fields, complete-packet and pair scores, masked reading errors and the predeclared policy gaps. Any scope-aware policy revision belongs in a separate matched study on further families. This question comparison keeps the policy fixed.
