# Report language: ML wording and Jev interpretation

October 2, 2026. The previous report classifier identified every domain but correctly read only 50/124 fault, normal or unknown states. “Service probes” appeared only in normal recovery training reports and pushed new fault descriptions toward normal. This study tests broader training language while preserving the classifier and fixed policy.

## Matched training change

Both report models fit the same 186 packets and 210 report annotations. Original phrases preserve the previous training input exactly. Broader phrases replace only observation detail; domain/reading annotations, packet targets, counts, timestamps, impact and topology stay unchanged. Method nouns and asset identifiers also stay unchanged. Each arm fits its own training-only word and character vocabulary with the frozen logistic settings.

The original power report says:

```text
Independent power tests at [asset] report that equipment supply is failing.
```

Broader training distributes six descriptions per domain/reading class and includes service-probe language across fault, normal and uncertain reports. Examples include:

```text
Fault:   equipment voltage is absent. Independent service probes confirm disruption.
Normal:  equipment voltage is normal. Independent service probes confirm continued service.
Unknown: equipment voltage loss is unconfirmed. Independent service probes cannot resolve the uncertainty.
```

These are examples of the phrase set, not a claim that those three reports have identical identifiers. The intervention changes several wording features together; it cannot isolate the effect of one word. The two report classifiers retain identical settings, report-level supervision and policy. The original 96-packet combined classifier remains a separate control.

## New development cases

The new pack contains 140 packets in 35 further families, forming 70 correlated pairs and 156 report annotations. Development packets, meanings and references are identical across training arms. Families cover paths, stale or unknown measurements, comparable contradictions, negation, uncertainty, missing inventory and clause scope. Restoration, unexplained work and unclassified messages provide controls.

One scoped-negation pair changes only report detail:

```text
A: A routine availability check passes, but the return-path interface drops traffic
   and delivery is disrupted.
B: A routine availability check passes, but the return-path interface does not drop
   traffic and delivery is intact.
```

Both packets retain current impact and a visible component relationship. The draft report annotations are transport/fault and transport/normal; the packet references assign transport in A and retain NOC in B. Passing an auxiliary check does not cancel the focal fault. Similarly, an unconfirmed earlier alarm does not cancel an independent current instrument's explicit fault measurement. These clause assumptions need specialist review.

The pack uses written teaching scenarios, literal domain prefixes and shared mechanisms. It is not representative network data or final held-out evaluation. Existing inspected development packets remain unchanged.

## Protocol and scoring

The local comparison fits original and broader report language once, then feeds their predicted meanings into the frozen policy. Frozen packet ML, frozen report expressions and original incident rules provide controls. All four packet decisions, pair success, report domain/reading accuracy, field regressions and incorrect readings hidden by correct triage remain separate measures. Reference annotations feed policy only in an evaluation diagnostic after actual predictions.

The Jev comparison uses these same development packets. Frozen selected-evidence direct triage retains its existing questions. A new text-only report request asks domain and fault/normal/unknown questions before feeding the same fixed policy used by report ML. This changes task boundaries, context and policy execution; it is an architecture comparison, not a question-only intervention. Exact inputs, question definitions, returned probabilities and policy traces are recorded. Direct triage retains software-priority and semantic-decision scores for comparison with calculated pipeline priority.

No model executes a network change. References, the 15-minute inclusive validity threshold and same-asset comparability remain provisional.

## Local result: broader wording loses ground

| Frozen approach | All four decisions correct | Both packets correct |
|---|---:|---:|
| Report ML · original phrases | 90/140 (64.3%) | 20/70 (28.6%) |
| Report ML · broader phrases | 86/140 (61.4%) | 18/70 (25.7%) |
| ML · frozen packet | 74/140 (52.9%) | 6/70 (8.6%) |
| Report rules → policy | 68/140 (48.6%) | 4/70 (5.7%) |
| Original incident rules | 72/140 (51.4%) | 4/70 (5.7%) |

Broader wording fixes four packets and loses eight that the original report model gets right. Each regression affects owner, next check and evidence sufficiency. Priority remains correct for every local arm because software calculates it from unchanged impact.

Domain accuracy improves from 92/156 to 156/156, but fault/normal/unknown accuracy falls from 76/156 to 72/156. Correct triage hides wrong report meanings in 38 original-wording packets and 28 broader-wording packets. Reading accuracy and packet accuracy answer different questions.

The intended shortcut weakens: the normal-minus-fault weight for “service probes” changes from +0.398 to −0.038. However, “service” rises from +0.398 to +0.710. The broader normal sentence repeats that word in “continued service.” This measured association suggests a replacement shortcut; it does not isolate the cause of the score loss.

Two cases show the tradeoff. In `NSL-65307fdfd0ed-b`, the capture “cannot establish whether delivery is disrupted.” Broader training introduces “cannot” and “whether”; their fitted contributions favor unknown. The reading changes from fault (37.6%) to unknown (54.2%), correctly retaining NOC. In `NSL-1772ea4f4a94-a`, the receiver “loses timing alignment and decoding stops.” The original classifier selects fault (46.5%); the broader classifier selects unknown (39.2%) and loses the correct RAN decision. Better domain identification does not repair that reading.

The frozen report expressions, which matched all 108 previous draft references, now match only 68/140 packets and 28/156 readings. Their earlier perfect score reflected coverage of familiar written phrases. I will retain the broader fit as a negative experiment rather than replace the original classifier.

[The local checkpoint](../checkpoints/report-language-local-2026-10-02.json) preserves scores, fitted term weights, matched changes and evidence fingerprints. [Open the inspection workbench](http://127.0.0.1:8768/report-language). Training view exposes both actual wordings. Development view follows reports through predicted meanings, policy joins and final decisions; references remain separately revealable. Exact inputs, saved vectors and fitted score margins are available for inspection and download.

## Jev result: separate interpretation helps, with one regression

All 296 requests completed with zero failures on `jev-1.13.0`: 140 direct-triage requests and 156 text-only report requests. Both architectures score the same 140 development packets.

| Jev architecture | All four decisions correct | Both packets correct |
|---|---:|---:|
| Frozen selected-evidence direct triage | 127/140 (90.7%) | 59/70 (84.3%) |
| Report interpretation → fixed policy | 139/140 (99.3%) | 69/70 (98.6%) |

The report pipeline fixes 13 direct-triage failures and loses one previously correct packet. Direct failures include uncertain measurements assigned a domain or domain diagnostic, normal readings treated as faults, and restored service sent to evidence gathering instead of monitoring. Calculated pipeline priority and direct Jev priority both match every reference, so priority does not explain this gain.

Jev identifies every report domain and matches 151/156 reading annotations. All five reading errors concern core reports that say the registration handler **accepts subscriber requests**. Jev selects unknown instead of the draft normal reading. Two different normalized report texts occur across these five rows; the domain prefix makes core explicit.

In `NSL-c9841c3176a5-a`, a current acceptance report and a current refusal report describe the same asset. Direct triage retains NOC. The report interpreter calls acceptance unknown and refusal fault; policy sees one supported fault without a recognized normal contradiction and assigns core, `inspect_core` and sufficient evidence. That is the sole packet regression. In four other packets, stale or otherwise ineligible normal reports, or a normal-only packet, keep final decisions correct despite the incorrect reading. The workbench exposes those intermediate errors rather than treating 139 correct packets as 139 understood incidents.

The [Jev checkpoint](../checkpoints/report-language-jev-2026-10-02.json) records every request fingerprint, returned choice and probability, policy trace and matched change. [Inspect the regression](http://127.0.0.1:8768/report-language?split=development&case=NSL-c9841c3176a5-a&arm=jev_reading#inspect), reveal the draft references, then select Report 1 and its reading probabilities. Jev gives unknown 64% and normal 36%. These are provider probabilities, not calibrated operational confidence or access to internal reasoning.

The gain supports further testing of separated interpretation and policy. It does not identify which architectural change caused the improvement, validate the draft annotations or establish performance on real telecom incidents. Earlier scores use other data packs and are not before/after deltas for this study.

## Repeatability check and the next decision

A bounded diagnostic replay repeated the two inspected acceptance texts and their matched refusal texts three times each: four distinct requests, 12 calls. The saved bodies and questions remain unchanged. Repetition checks whether the same readings recur; it introduces no new families and cannot estimate independent accuracy. The [replay protocol](../checkpoints/report-language-replay-protocol-2026-10-02.json) records that selection before calls.

All 12 calls completed with zero failures. The first acceptance wording produced unknown, normal, unknown; the second produced unknown in every repeat. Both matched refusal texts produced fault in every repeat. Agreement with the draft meanings was 2/4, 3/4 and 2/4 reports across the three repetitions. Those are four selected texts, not 12 independent scenarios or a revised score for the 140-packet evaluation. The [replay checkpoint](../checkpoints/report-language-replay-2026-10-02.json) preserves exact bodies, raw replies, probabilities and per-text agreement. The workbench shows these repetitions separately from original predictions.


On October 2, the user selected **normal handler reading**: request acceptance establishes normal operation of the measured handler, while registration completion remains separate. This confirms the existing draft boundary and preserves every recorded reference. The next matched question experiment will clarify the measured-function scope on new development families.

I will keep the current models, questions, policy and references frozen. New development families will contrast request acceptance, completed registration, partial success and uncertain completion. Training changes belong in a separate matched study; specialist-reviewed references and new held-out families must precede any operational claim.

## Reproduce

```bash
uv run --locked python -m scripts.run_report_language validate
uv run --locked python -m scripts.run_report_language run --output runs/report-language/my-local-study
uv run --locked python -m scripts.run_report_language verify --output runs/report-language/my-local-study
```

Raw evidence stays under ignored `runs/report-language/`; runs refuse overwrites. The historical public bundle remains unchanged. Hosted requests use the pinned Jev checkpoint and a server-side key, with no automatic retries.

The [prepared protocol](../checkpoints/report-language-protocol-2026-10-02.json) records source and data fingerprints before inference. Eleven preflight tests check matched data, report/policy boundaries, fitted explanations, request recording, credential redaction, stop conditions and failure-inclusive denominators. Jev requests follow the [TypeSafe Choice API](https://docs.typesafe.ai/introduction/quickstart). The hosted run completed all 296 planned calls. Its verification recomputes report readings, packet policy traces and failure-inclusive scores.


```bash
uv run --locked python -m scripts.run_report_language_jev preflight
uv run --locked python -m scripts.run_report_language_jev run --output runs/report-language-jev/my-hosted-study
uv run --locked python -m scripts.run_report_language_jev verify --output runs/report-language-jev/my-hosted-study
```

The diagnostic replay requires its original saved hosted run under `runs/report-language-jev/development-2026-10-02-v1/`. It verifies that evidence before reusing exact request bodies. A fresh clone cannot recreate this replay selection from scores alone.


```bash
uv run --locked python -m scripts.run_report_language_replay preflight
uv run --locked python -m scripts.run_report_language_replay run --output runs/report-language-replay/my-diagnostic
uv run --locked python -m scripts.run_report_language_replay verify --output runs/report-language-replay/my-diagnostic
```

[The reference decision brief](report-language-review.md) gives the two readings to choose between and the implications for new cases. Existing references and scores remain unchanged.
