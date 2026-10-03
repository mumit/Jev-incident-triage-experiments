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

The subsequent Jev comparison will use these same development packets. Frozen selected-evidence direct triage will retain its existing questions. A new text-only report request will ask domain and fault/normal/unknown questions before feeding the same fixed policy used by report ML. This changes task boundaries, context and policy execution; it is an architecture comparison, not a question-only intervention. Exact inputs, question definitions, returned probabilities and policy traces will be recorded. Direct triage retains software-priority and semantic-decision scores for comparison with calculated pipeline priority.

No model executes a network change. References, the 15-minute inclusive validity threshold and same-asset comparability remain provisional.

## Reproduce

```bash
uv run --locked python -m scripts.run_report_language validate
uv run --locked python -m scripts.run_report_language run --output runs/report-language/my-local-study
uv run --locked python -m scripts.run_report_language verify --output runs/report-language/my-local-study
```

Raw evidence stays under ignored `runs/report-language/`; runs refuse overwrites. The historical public bundle remains unchanged. Hosted requests will use the pinned Jev checkpoint and the existing server-side key, with no automatic retries.

The [prepared protocol](../checkpoints/report-language-protocol-2026-10-02.json) records source and data fingerprints before inference. Eleven preflight tests check matched data, report/policy boundaries, fitted explanations, request recording, credential redaction, stop conditions and failure-inclusive denominators. Jev requests follow the [TypeSafe Choice API](https://docs.typesafe.ai/introduction/quickstart). The hosted preflight plans 140 direct requests plus 156 report requests, for 296 calls.
