# Declared domain, model readings and software

## Definition and question

On October 2, 2026, the user selected **declared instrument domain**. The domain identifies the instrument’s stated source, not a root cause inferred from technical vocabulary. Policy separately checks whether its current fault has a visible path to affected service. A missing or ambiguous declaration establishes no domain.

The [metadata study](metadata-policy.md) remains frozen. Its RAN and power disagreements exposed a mismatch between draft references that accepted source prefixes and a Jev question that described technical functions. This new study versions the selected task definition on further families. Comparing the two questions measures agreement with that definition; it does not prove the earlier technical-domain question was wrong under its own meaning.

## Matched Jev questions

Both Jev arms receive the same normalized report text, including an explicit `Instrument domain` header. The technical-domain control copies the frozen measured-function request. The candidate changes only the domain question’s instructions and choice descriptions. The model, state, fault/normal/unknown question, context limit and metadata policy stay fixed. Instructions and criteria change together, so their individual effects cannot be separated.

For example, both requests receive:

> Cross-system instrument observation. Instrument domain: ran. The focal monitored operation records an internal component failure; the measured operation cannot execute correctly. Context only: the incident ticket also mentions electrical supply. That separate function is not measured in this report.

The control describes RAN through radio processing, decoding, timing or equipment measurements. The candidate asks:

> Identify the single explicitly declared instrument domain in this report, not a fault domain inferred from its technical vocabulary. Use the Instrument domain declaration. Other domains mentioned as context or separate functions do not replace that declaration. If the declaration is unavailable, ambiguous, missing or invalid, select none.

Its `ran` choice means that the instrument explicitly declares its single domain as `ran`. The `none` choice covers a missing, unavailable, ambiguous or invalid declaration. The reading question remains unchanged, including the focal-function instruction from the preceding study. Changing one question may still affect the other returned answer; report-reading regressions will be scored separately.

Jev receives neither structured declaration metadata nor measurement scope, paths, impact, timestamps or references. It sees the declaration in the report text. The workbench will expose exact before/after requests and choice definitions.

## Software-domain controls

Each observation also supplies the same declaration in a structured field:

```json
{"instrument_domain": {"status": "declared", "domain": "ran"}}
```

A software control reads only this field. It copies a valid single domain, otherwise returns `none`. It does not read report prose, identify a fault, inspect reference answers or decide an owner. Each Jev and local interpreter gets a software-domain path that retains its actual fault/normal/unknown prediction while replacing only domain. These paths make no additional model calls and assign no invented domain probabilities.

The structured declaration and prose header agree by construction. This is an explicit synthetic assumption. The software comparison tests whether interpreting a supplied category is useful; it does not validate the category’s provenance or accuracy. Failed or missing reader responses remain failed even when software can supply domain.

## Data and frozen controls

The pack contains **64 development packets, 128 report occurrences, 16 new families and 32 pairs**. Thirty distinct normalized texts supply these correlated occurrences. Two graph/impact variants share each family’s wording. Their degraded-service impacts cover one or 12 sites; the existing priority calculation yields P3 or P2.

Four families use generic operation outcomes. Four add another domain’s technical vocabulary as context. Two withhold the instrument declaration while describing radio or electrical functions; the selected definition still assigns `none`. Two make the declaration unresolved between core and transport. Four change fault currentness or dependency eligibility.

Function-comparison pairs change only the normal report’s scope function: a different function permits the observed fault, while the same function creates a contradiction. Missing/ambiguous pairs change arrival time without changing NOC. Eligibility pairs make the fault stale or disconnected while keeping its written meaning unchanged. Every pair preserves report text and its separate prewritten domain/reading annotations.

Original-phrase ML, broader-phrase ML and report rules remain frozen controls. Both ML models reuse their earlier 210-report train-only recipes. No new training, vocabulary tuning or annotation changes occur here. Their software-domain paths preserve the same reading predictions.

All report and packet references are written before inference and remain drafts. No held-out set exists. Generic templates, explicit headers and consistent metadata make this a teaching comparison, not a realistic network sample.

## Prepared diagnostic and execution

Prewritten report meanings fed to the frozen metadata policy match all **64/64** packet references. This diagnostic checks the intended intervention before inference. It is neither model performance nor an accuracy ceiling.

The [protocol](../checkpoints/declared-domain-protocol-2026-10-02.json) records source/data fingerprints, both question sets and a plan for **60 serial Jev calls**, alternating question order by distinct text. Each actual response joins all occurrences of its text, including paired packets. These are 30 distinct inputs per question, not 128 independent model observations.

Requests, inputs and separate references are saved before calls. New run directories refuse overwrites. There are no warmup calls or automatic retries. Access, configuration, rate-limit, checkpoint and network errors stop the run; three consecutive malformed responses also stop it. Shared failures invalidate every dependent packet and software-domain path. Scores keep the full denominators.

```sh
.venv/bin/python -m scripts.run_declared_domain validate
.venv/bin/python -m scripts.run_declared_domain preflight
.venv/bin/python -m scripts.run_declared_domain local --output runs/declared-domain/development-2026-10-02-v1
.venv/bin/python -m scripts.run_declared_domain hosted --output runs/declared-domain-jev/development-2026-10-02-v1
.venv/bin/python -m scripts.run_declared_domain verify --output runs/declared-domain/development-2026-10-02-v1
.venv/bin/python -m scripts.run_declared_domain verify --output runs/declared-domain-jev/development-2026-10-02-v1
```

Local evidence includes predictions, 60 distinct-text ML vectors and 120 fitted margins. Hosted evidence records exact requests, responses, returned distributions, latency and joins. Raw runs remain ignored and are outside the historical public bundle. A fresh clone can replay local controls; new hosted runs need a server-side key and incur charges.

## Results

All **60 Jev calls completed without failures** from frozen preparation commit `0d5c214`. Both raw runs verify. The [hosted checkpoint](../checkpoints/declared-domain-jev-2026-10-02.json) and [local checkpoint](../checkpoints/declared-domain-local-2026-10-02.json) retain interpretation scores, matched changes, field regressions, attribution and fingerprints.

| Reader | Interpreter domain: packets match | Software domain: packets match | Interpreter / software: complete pairs match |
|---|---:|---:|---:|
| Jev · technical-domain question | 56/64 | 64/64 | 28/32 / 32/32 |
| Jev · declared-domain question | 64/64 | 64/64 | 32/32 / 32/32 |
| Report ML · original phrases | 40/64 | 40/64 | 8/32 / 8/32 |
| Report ML · broader phrases | 40/64 | 40/64 | 8/32 / 8/32 |
| Report rules | 44/64 | 64/64 | 16/32 / 32/32 |

The declared-domain question fixes eight packets and loses none against the technical-domain control. It corrects four distinct domain annotations, covering the two fault/normal texts for each missing-declaration family. The control identifies RAN from radio decoding and power from electrical supply. Those are reasonable technical domains under its frozen definition, but the selected declaration definition requires `none`. This gain measures compliance with the chosen task; it does not prove general domain-reasoning improvement.

Both Jev questions read all **30/30** distinct operation outcomes correctly. Domain agreement is 26/30 for the control and 30/30 for the candidate. Neither question has wrong report meanings hidden by matching packet decisions. Technical distractions and ambiguous declarations already pass under the control; no observed gain can be attributed to those cases. The explicit headers differ from the preceding pack, so this study cannot isolate their effect from a cross-study score comparison.

The software-domain control fixes the same eight packets while retaining the technical-domain reader’s actual fault/normal predictions. It changes none of the declared-question packets. Neither intervention introduces a newly wrong owner, priority, diagnostic, evidence or report-reading field. Supplying domain in software achieves the selected task here without additional Jev calls. This does not validate declaration trust or prove that a reading-only Jev request would behave identically: both hosted requests still ask for domain and reading.

### Why software domain does not rescue ML

Both frozen ML models return `unknown` for all 30 distinct report texts. Neither has a correct operation-outcome annotation; domain agrees on only 6/30. The software control corrects domain to 30/30 but preserves those unknown readings. Every ML path retains NOC on all 64 packets, matching the 40 NOC references and missing all 24 domain-owner references. All 40 packet matches therefore hide report disagreements.

The saved broader-phrase ML score for the generic core normal report selects unknown at 62.5%, versus normal at 24.5%. Its unknown-versus-normal log-odds margin is 0.934. `instrument`, `the` and `domain` contribute approximately +0.229, +0.216 and +0.181, while `normal` contributes -0.072. Generic framing learned from the frozen training set outweighs the normal token in this particular fitted score. These weights explain the classifier’s output, not a physical cause or a universal failure mechanism. More training phrases would need a separate matched study on new families.

Report rules recognize every fault/normal outcome on this explicit `failure`/`normal` wording, but match only 14/30 declared domains. Copying domain fixes 20 packets and loses none relative to the rule reader, reaching 64/64 with no hidden report disagreements. The rule expression and its vocabulary remain unchanged. This result is specific to the deliberately simple wording and reliable synthetic declarations.

### Limits and next boundary

The candidate and software-domain paths pass the stale/unlinked fault controls and preserve NOC when declarations are missing or ambiguous. Full packet agreement remains agreement with drafts on controlled development cases; no specialist review, final held-out set, repeatability check or operational validation has occurred.

The pack makes structured declarations agree with report headers. A real adapter may receive contradictory declarations or stale instrument metadata. Before the next trust comparison, its reference policy must specify which source is authoritative when structured metadata and an explicit prose declaration disagree. That decision changes input handling and owner references; it cannot be chosen from these scores.

## Inspecting the comparison

Open `/declared-domain` or **Comparison → Declared instrument domain**. Select the report interpreter and domain source independently. Switching to software domain preserves the selected reader’s operation readings and exact request. The page shows raw structured declarations, both Jev question definitions, actual responses, fixed policy joins and ML score contributions. Draft references remain hidden until requested, and browsing makes no model calls. A fresh clone without raw runs reports missing predictions explicitly.

[The declaration-trust brief](declaration-trust-review.md) describes the next required policy choice with a hypothetical conflicting input.
