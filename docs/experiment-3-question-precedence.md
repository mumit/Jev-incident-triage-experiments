# Experiment 3: question precedence

October 2, 2026. This development comparison tests whether explicit evidence rules help Jev use the dependency and measurement facts already supplied. References remain drafts. The [first input comparison](experiment-3-development.md#jev-development-results) and all historical evidence stay unchanged.

## Decision and scope

I kept NOC as the first investigating team until current evidence links a fault to an affected service. This is the user-selected rule for the synthetic study, not specialist validation of a real operating policy.

The first comparison supplied useful facts but left their precedence implicit. For example, the original question says a directly observed malfunction is enough to begin domain investigation. That leaves unclear whether a current fault with an unknown incident relationship warrants a domain assignment. This comparison makes the relationship requirement explicit.

The 15-minute validity window, same-bus conflict rule and scenario realism still need network-specialist review. No final held-out set exists. A successful development result would support further testing of the wording, not operational adoption.

## What changes in the request

Both arms receive **exactly the same combined state string**, including raw topology, dependency facts and measurement-age facts. Both use `jev-1.13.0`, the unchanged Northstar policy, identical valid choices and the original priority question. Only the instructions for owner, next check and evidence sufficiency change.

| Arm | Instructions |
|---|---|
| Original questions | The frozen experiment 2 focused questions, used in the first experiment 3 comparison. |
| Explicit evidence precedence | Current measurement and a supporting affected-service path must precede domain assignment. Comparable current conflicts leave the domain unresolved. A partial map can support a visible path; missing or excluded relationships cannot justify assignment. |

The original owner instruction includes:

```text
A directly observed malfunction is enough to begin domain investigation even if its exact cause is unknown.
```

The revised instruction adds concrete tests:

```text
Join observations and both calculated fact blocks by observation_index.
An observation supports a domain only if it reports that domain's malfunction,
its measurement_facts freshness_status is current, and dependency_facts supplies
at least one supporting path from a listed affected site to that observed asset.
If no unique domain remains supported, retain noc, gather_evidence and
insufficient_evidence=yes.
```

The complete request remains inspectable. The revised questions do not contain a packet's reference answers or family identity. This comparison tests the three instruction changes together; it cannot identify which sentence causes a gain or regression. It also does not change ML inputs, features or training.

## New development cases

The separate `data/experiment-3-question-draft/` pack contains 16 packets in eight pairs across eight new written families. It contains no training or held-out split. Each pair changes exactly one declared field; six pairs should change a decision and two should remain stable.

| Family | Controlled change |
|---|---|
| Regional queue isolation | A complete service path stops reaching the faulty transport component. |
| Timing register expiry | A radio measurement becomes stale while report arrival stays recent. |
| Battery distribution inventory | The dependency map becomes unavailable despite a current power fault. |
| Session registry timestamp | A core trace loses its measurement timestamp. |
| Comparable bus samples | A nominal reading becomes stale, leaving a current zero-voltage reading. |
| Spare rack inventory | An unrelated edge is added without changing the supported transport path. |
| Partial branch evidence | A visible path disappears from a partial map, leaving an unknown relationship. |
| Receiver report transit | Arrival changes while the measurement remains current and related. |

These patterns use the same constructed vocabulary and teaching assumptions as the earlier pack. New family names and wording do not establish independence from the generator's assumptions or realism. The references were written before hosted inference and remain separate from inputs. Later revisions need further development cases.

## Run controls

The comparison has a maximum of **32 hosted requests**: 16 packets times two question arms. Serial execution alternates arm order by packet, with no warmup or automatic retries. The preflight checks the fixed checkpoint and declared context bound. Every request, reference and source fingerprint is saved before inference.

Configuration errors, rate limits, checkpoint mismatches and network errors stop the run immediately. Three consecutive invalid responses also stop it. Failed and unattempted requests stay in the score denominator. Existing runs cannot be overwritten; keys remain server-side and outside exports. Provider charges apply.

Compare individual decisions, all-four accuracy, both-packet accuracy, fixes and regressions on these same packets. Record high-probability errors. Do not subtract these scores from the earlier 36-packet comparison: the data differ, and the original-question arm here is the matched control.

## Results

Run `development-2026-10-02-v1` completed all 32 requests with zero failures. Every response reported `jev-1.13.0`. The [machine-readable report](../checkpoints/experiment-3-questions-2026-10-02.json) records the fixed requests, source fingerprints and full metrics. The app checks those fingerprints and recomputes scores before showing saved responses.

| Jev questions | All four correct | Both packets correct | Owner | Next check | Evidence |
|---|---:|---:|---:|---:|---:|
| Original | 56.3% (9/16) | 25.0% (2/8) | 62.5% | 62.5% | 68.8% |
| Explicit precedence | 93.8% (15/16) | 87.5% (7/8) | 93.8% | 93.8% | 93.8% |

Priority is correct on every packet. Explicit precedence fixes six packets without losing a previously fully correct packet. It gets five of the six decision-changing pairs fully correct; original questions get none. Both arms pass the two invariance pairs.

The fixes span complete-path exclusion, a stale radio measurement, missing inventory, a missing core measurement timestamp, current voltage conflict and an unsupported path in a partial map. The original questions often route to the observed domain despite the unusable measurement or missing incident relationship. Explicit precedence instead selects NOC, gathers evidence and marks evidence insufficient, matching the selected teaching rule.

### Remaining failure and regression

Both arms miss [comparable bus samples B](http://127.0.0.1:8768/experiment-3?trial=questions&split=development&case=NSQ-4b1b04a8a39c-b&variant=precedence#decisions). A zero-voltage reading is four minutes old; the nominal reading is 73 minutes old. Both fact blocks identify their ages and supported service paths. The revised instructions explicitly exclude the stale reading from a current conflict, but Jev still chooses NOC, gather evidence and insufficient evidence.

Original questions select power correctly on that packet while missing the diagnostic and evidence disposition. Explicit precedence introduces an **individual owner regression**, choosing NOC with 89% selected-answer probability. Its diagnostic probability is 89% for gathering evidence, and insufficient evidence receives 83%. These values are uncalibrated. An aggregate gain does not eliminate individual regressions.

### Interpretation

This matched result supports the hypothesis that explicit decision precedence can help Jev apply the supplied facts. It does not prove that implicit precedence caused the first comparison's failures: this pack differs, and the three instruction changes happened together. A single response per packet and arm also leaves response variability unmeasured.

I will retain the revised questions as a development candidate. The remaining conflict failure needs further cases that distinguish comparable current conflicts from stale contradictory reports, with both quantity and operating conditions clear. Specialist review must still validate the references and validity windows. A separate ML comparison of structured dependency and age features remains pending.

Before a final evaluation, freeze reviewed references, questions and transformations and use new held-out families. These 16 packets have now informed the interpretation and cannot serve as an untouched test of later revisions.

[Open the question workbench](http://127.0.0.1:8768/experiment-3?trial=questions) and choose an arm. **Exact input** shows the original and selected question definitions side by side; the complete request includes their shared state. **Decisions** exposes saved choices, probabilities, requests and returned responses. **Comparison** switches back to the earlier input-facts comparison. A fresh clone exposes missing predictions explicitly; the tracked report does not substitute for raw evidence.

## Reproduce

```bash
uv run --locked python -m scripts.run_experiment3_questions validate
uv run --locked python -m scripts.run_experiment3_questions preflight
uv run --locked python -m scripts.run_experiment3_questions run --output runs/experiment-3-questions/my-comparison
```

The checked-in pack is already built. `build` only creates a new pack when its destination does not exist. Hosted runs need your own key in the environment or ignored `.env`; the CLI does not read a key held only in another server's memory.

## Subsequent recurrence check

The [conflict repetition](experiment-3-conflict-repetition.md) adds four new conflict pairs and three repeats of both frozen question sets. Explicit precedence retains the same stale-conflict error on every family and repetition. It gets the current-conflict side right, but regresses the stale side's owner. The original 32-request run remains unchanged. The next comparison will test software evidence eligibility and selection before conflict comparison, using further cases and the same questions.
