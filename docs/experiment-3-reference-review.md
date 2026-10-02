# Experiment 3 reference review and Jev run plan

## Review status

I checked the draft pack's structure, controlled changes and available input information. This review does not replace a network specialist's assessment. The answer keys remain unchanged and explicitly provisional. No final held-out set exists.

The pack validator confirms 72 training and 36 development packets, disjoint families, complete pairs, separate references and matching fingerprints. Priority matches the existing policy. Every pair changes exactly its declared field. The 18 development pairs comprise 14 decision changes and four invariance checks.

### Information available to a model

Eight pairs have identical compact-baseline requests but different draft answers. The dependency-only variant has the same limitation. Both discard measurement time, so they cannot distinguish current, stale or missing measurements in those pairs. The measurement and combined variants preserve that distinction in calculated facts.

This is an information-availability comparison as well as a representation comparison. A gain on those pairs would show the value of supplying a missing fact; it would not establish better reasoning over identical evidence. Conversely, inconsistent decisions on identical inputs may reflect response variability, not sensitivity to the changed raw timestamp.

### Decisions needing specialist review

| Question | Cases to inspect | Current draft assumption |
|---|---|---|
| When does a measurement stop supporting an initial diagnosis? | Roof supply display, resolver trace delay | Each telemetry type declares a 15-minute validity window. Five minutes is current; 95 minutes is stale. This window has not been operationally validated. |
| Does a missing measurement timestamp require fresh evidence even when the report just arrived? | Sector sample without time | Retain NOC, gather evidence and mark evidence insufficient. Report arrival does not establish measurement time. |
| Should an observed malfunction justify domain investigation when a complete map excludes it from the affected service? | Relay detour, exchange uplink map | Retain NOC after the path moves away from the faulty component. The existing Choice wording also says a directly observed malfunction supports initial investigation, so the relationship requirement needs explicit review. |
| What changes when topology is missing or partial? | Inventory not delivered, feeder excerpt | Missing topology does not establish a relationship. A partial map can support a visible path but cannot prove absence. The draft retains NOC when no supported incident relationship remains. |
| Do two current, independent voltage readings conflict enough to prevent domain assignment? | Supply feed disagreement | Retain NOC when zero and nominal readings conflict. A 95-minute-old nominal reading does not contradict the current zero-voltage reading. Check whether the sensors observe the same bus and comparable conditions. |
| Is an irrelevant inventory edge sufficient as an invariance control? | Archive edge append | The supported service path and decisions remain unchanged. Review whether the written diagnostic evidence warrants the chosen check independently of the topology. |

The topology teaching model declares directed **required service dependencies** and complete or partial coverage. It does not model protection switching, redundancy, capacity or inventory reliability. A path supports a relationship, not a confirmed cause. These omissions limit transfer to a real network.

No review flag changes an answer key or accepts a model's answer after seeing the result. If specialist feedback changes references, it needs a new version and a separately identified re-score. The existing draft scores must remain available.

## Bounded Jev development comparison

Run `development-2026-10-01-v1` completed all 144 requests with zero failures. [The development results](experiment-3-development.md#jev-development-results) record scores and regressions. The controls below describe that run and its reproduction.

The first hosted run used all 36 development packets and four variants: compact baseline, dependency facts, measurement age and both. It has a maximum of **144 requests**. Training packets do not enter hosted evaluation, and no model fitting or question tuning occurs during the run.

Controls:

- Keep `jev-1.13.0`, the existing policy and focused Choice definitions fixed.
- Retain the same packets and provisional answers used by the local comparison. Keep references out of requests.
- Save every exact request, input, answer-key fingerprint and implementation fingerprint before the first hosted call.
- Execute serially and rotate variant order across packets to distribute early and late positions. Do not warm up or retry automatically.
- Check the existing conservative context bound: UTF-8 request bytes plus 512 must fit the declared capacity. This is not the provider's tokenizer.
- Stop immediately for configuration/access errors, rate limits, a reported checkpoint mismatch or a network failure. Otherwise stop after three consecutive failed responses. Keep failed and unattempted responses in the score denominator.
- Save returned choices, probabilities, reported model, usage, latency and responses in a new ignored run directory. Redact credentials and never overwrite a run.

Provider charges apply. The request limit bounds calls, not currency cost. The run records returned usage rather than claiming a price estimate.

### Reproduction

Use the existing server configuration or an ignored `.env` with your own key. The CLI reads the same environment settings as app startup; it does not read a key stored only in another server's memory.

```bash
uv run --locked python -m scripts.run_experiment3_jev preflight
uv run --locked python -m scripts.run_experiment3_jev run --output runs/experiment-3-jev/my-first-comparison
```

For a smaller diagnostic run, use `--pair` with an existing pair ID. Each selected pair retains both packets and all four variants. A new output directory is required each time.

## Reading the results

Compare Jev's four variants within this draft pack and against the corresponding local ML inputs. Retain all four outputs and inspect both-record pair accuracy, regressions, contradictory decisions and high-probability errors. Provider probabilities remain uncalibrated for operations.

All reported scores are against draft references. Disagreement in the flagged cases may reveal a reference assumption or question ambiguity rather than a model failure. This development run cannot establish operational performance or an improvement over historical scores. Further changes need new development cases; reviewed references and frozen transformations must precede a new held-out evaluation.

## Subsequent question comparison

On October 2, the user selected NOC retention until current evidence links a fault to affected service for the synthetic study. That resolves the intended teaching disposition, not specialist review of a real network policy. The [question-precedence comparison](experiment-3-question-precedence.md) records the exact instruction changes and a separate 32-request run on new development cases. The original answer keys and 144-request comparison remain unchanged.

The [repeated conflict check](experiment-3-conflict-repetition.md) preserves both question sets and confirms the stale-conflict failure across four further pairs and three repetitions. It adds recurrence evidence while leaving specialist review, the original references and earlier runs unchanged.

The [evidence-selection comparison](experiment-3-evidence-selection.md) completed 36 requests on a further 12-packet pack. Its freshness-and-visible-path filter improves agreement with draft references, but the eligibility rule and loss of contextual evidence also need review. Check that missing timestamps, inventory gaps and domain-specific validity windows should exclude a reading, and whether multiple current faults require a different disposition. Preserve recorded references and software while developing further controls.

The [selection-robustness check](experiment-3-selection-robustness.md) completed 48 calls on eight new packets, repeating both frozen inputs three times. Selected observations match all eight draft references in every repeat; combined facts match seven. Selection fixes one validity-boundary packet, repeated three times, and introduces no new wrong fields. Both inputs pass the partial-inventory, missing-inventory and multiple-domain controls and keep identical decisions across repeats. The multiple-domain reference remains provisional; agreement does not establish correctness or operational reliability. Review whether one visible affected-service path is enough to assign an initial owner, what unknown inventory should imply, and how to sequence investigation when two domains have current supported faults. Preserve the prewritten references when reviewing these results.

The [structured ML comparison](experiment-3-structured-ml.md) fits four matched classifiers on 96 new training packets and scores 64 development packets. Both feature blocks together match 52/64 draft references versus 24/64 for the text baseline, with 20/32 versus 6/32 pairs correct. It fixes 28 complete packets and loses none, but introduces eight wrong owner fields and ten wrong diagnostic fields on already-failed packets. Current transport faults still receive NOC at about 85% probability. Jev makes no calls in this comparison. Review current independent-fault wording as well as dependency/freshness assumptions. The new fitted probabilities and channel weights remain learning artifacts, not operational confidence or specialist signoff.

The subsequent [training-wording study](experiment-3-wording.md) keeps the structured ML recipe fixed. Its negative matched result and new power-owner regressions motivated the completed [report-policy comparison](experiment-3-interpretation.md). Its observation annotations, comparable-report grouping and recovery assumptions also need review. The recorded Jev questions and inputs remain unchanged.
