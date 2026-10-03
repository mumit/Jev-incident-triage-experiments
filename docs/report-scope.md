# Measured-function reading experiment

## Question and controls

I selected **normal handler reading** on October 2, 2026: successful request acceptance establishes normal operation of the measured handler, while registration completion remains a separate measurement. This synthetic teaching decision preserves the earlier report references; it does not establish specialist review.

This comparison tests whether an explicit reading instruction helps Jev distinguish success, malfunction and uncertainty **at the function named in a report**. Both arms receive identical new report texts, domain questions, choice criteria and the pinned `jev-1.13.0` model. Their returned meanings feed the same frozen policy. Only `questions.reading.instructions` changes.

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

## Results

All 176 hosted calls completed without failures. Both runs verify against the frozen setup in commit `2f65910`. The [local checkpoint](../checkpoints/report-scope-local-2026-10-02.json) and [Jev checkpoint](../checkpoints/report-scope-jev-2026-10-02.json) retain scores and error identifiers.

| Path | Domain correct | Reading correct | Both report fields correct | All four packet decisions correct | Complete pairs correct |
|---|---:|---:|---:|---:|---:|
| Jev · original report question | 88/88 | 82/88 | 82/88 | 67/68 | 33/34 |
| Jev · measured-function question | 88/88 | 83/88 | 83/88 | 68/68 | 34/34 |
| Report ML · original phrases | 10/88 | 14/88 | 0/88 | 46/68 | 12/34 |
| Report ML · broader phrases | 88/88 | 12/88 | 12/88 | 46/68 | 12/34 |
| Report rules → policy | 88/88 | 12/88 | 12/88 | 46/68 | 12/34 |

The added Jev instruction fixes two report readings and loses one. It fixes one packet and loses none; no packet field becomes newly wrong. These are single responses on correlated development templates, not evidence of a repeatable gain.

### What changed and what remained wrong

The explicit receipt trace in `NSS-562afee7c471-a` changes from unknown to normal. Successful completion in report 2 of `NSS-be3b5d951cb0-b` also changes from unknown to normal. Recognizing that completion success conflicts with the same-function completion fault restores the draft NOC decision.

The regression is `NSS-ec1b69ec4685-a`: a handler that acknowledges receipt and accepts correctly formed requests changes from normal to unknown. The measured-function arm returns equal 0.50 probabilities for normal and unknown and selects unknown. The stored choice remains the prediction; the lab does not reinterpret the tie. The packet still retains NOC because the service remains degraded without an explanatory fault.

Both arms continue to call the intake report in the intake-versus-completion-scope pair unknown, despite its explicit intake scope. Both also call successful intake unknown in the two different-function packets. The instruction therefore does not resolve the selected meaning boundary consistently.

### Why 68/68 does not mean the pipeline is correct

Five packets in each Jev arm receive correct triage despite a wrong report reading. In the measured-function arm, these include **both predeclared policy gaps**. Calling successful intake unknown prevents the policy from recognizing a normal/fault combination; it then assigns core, matching the draft packet decision for the wrong intermediate reason.

Feeding the correct normal intake reading to the same policy would instead retain NOC, exposing its inability to distinguish intake from completion. The 68/68 packet result therefore combines genuine fixes with hidden reading and policy errors. Neither arm has a recorded packet with all report readings correct and triage wrong on this run, because both misread the intake reports that would reveal the gap.

### What the ML controls show

The original report model selects domain none on 78/88 reports and unknown on 78/88 readings. The broader model recognizes all explicit domains but selects unknown on 84/88 readings. The rule reader also selects unknown on 84/88 readings; its fixed expression list does not cover most new measurement descriptions.

Saved ML margins make one shortcut concrete. For the first intake report, original ML favors none over core with an intercept difference of +1.770 and a +0.303 contribution from the repeated word `instrument`, outweighing the available core-related terms after other contributions. This explains that fitted score, not a causal account of the physical network. Both ML models predict unknown on this report.

All three local paths retain NOC on every packet and achieve 46/68 agreement through those identical fallback decisions. Original ML hides wrong readings in all 46 correct packets; broader ML and report rules hide them in 34. The unchanged triage scores therefore obscure large differences in report understanding. These controls were frozen before this pack, so the result measures transfer to new wording rather than a newly trained matched ML candidate.

## Next decision

The next policy comparison needs a source for **which function each instrument measures**. A field such as `measured_function: request_intake` could come from a maintained instrumentation schema. Alternatively, a reader could extract it from free text, with its own uncertain and missing outputs. Those are different input assumptions and failure modes. Neither source is established by this synthetic pack.

For a metadata-first study, a supplied field might identify report 1 as `measured_function: registration_completion` and report 2 as `measured_function: request_intake`. These fields describe instrumentation scope, not fault status or a reference answer. Missing or ambiguous scope needs an explicit control rather than an assumed function.

I will keep this question study frozen. Before constructing the next pack, the measurement-scope source needs a decision. A separate comparison can then group contradictory readings by domain, asset and compatible measurement scope, preserving NOC when scope or comparability is unknown. New families, separate report annotations, missing-scope controls and specialist review remain necessary. The current drafts do not establish operational readiness.

## Inspection workbench

Open [the measured-function workbench](http://127.0.0.1:8768/report-scope) or choose **Comparison → Measured-function reading**. The result view keeps report and packet scores separate, with links to report fixes, a regression and both known policy gaps. Select a family, pair, packet, interpreter and report to follow raw evidence through meanings and the selected policy trace.

The exact-input section compares both complete Jev reading instructions and exports the selected request. ML inspection shows saved vectors and fitted contributions; Jev inspection shows actual returned distributions and responses. Revealing references also displays the reference-reading-fed policy diagnostic, clearly separate from model predictions. The guide preserves the selected inspection context. Browsing makes no model calls, and a fresh clone shows unavailable results explicitly.
