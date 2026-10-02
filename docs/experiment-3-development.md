# Northstar Telecom: experiment 3 development

October 1, 2026. This is a local development pilot with **draft references**, not a final evaluation. Jev has not run on this pack. The [historical baseline](current-state.md), frozen inference and recorded results remain unchanged.

## Purpose

I am testing whether explicit dependency and measurement-age facts help models apply the existing incident policy. Experiment 2 changed several things together. This comparison keeps the policy, Jev checkpoint and questions fixed and varies only the input representation.

[Open the experiment 3 workbench](http://127.0.0.1:8768/experiment-3) to inspect a controlled pair. Follow **Raw evidence → Calculated facts → Exact input → Decisions**. Switch between packets A and B and the four input variants. Draft references stay separate and hidden until revealed; missing Jev results remain explicit.

## New data

The separate `data/experiment-3-draft/` pack contains 72 training packets across 12 families and 36 development packets across nine families. Each family is a manually specified scenario pattern. Its variations are correlated, not independent network incidents. Family names and reference decisions live in the answer keys, outside model inputs.

Each pair changes one declared field: topology edges, topology coverage, the availability of the map, a measurement timestamp or report arrival. The references specify whether that change should alter a decision or leave it stable. Training and development families are disjoint. Development uses different dependency layouts and wording, but the examples still share a constructed vocabulary and assumptions.

The pack covers related and unrelated transport faults, missing or incomplete inventory, stale or missing measurement times, conflicting voltage reports and irrelevant inventory changes. Training also includes report delivery, recovery and maintenance cases. There is **no new held-out set**. Once development failures influence a revision, these cases cannot serve as its final test.

These are teaching cases, not samples from a real network. A network specialist still needs to review:

- Whether directed edges describe required service dependencies, including the effects of protection, redundancy and inventory gaps.
- Whether affected-site identities and independent service checks support the stated incident scope.
- Appropriate validity windows for each telemetry type. Every observation currently declares 15 minutes; that is a teaching assumption, not an operational threshold.
- Diagnostic alternatives when evidence conflicts or the affected component has no known relationship to the impacted service.

## Four controlled inputs

| Variant | Input change |
|---|---|
| Compact baseline | The frozen experiment 2 compact transform, applied to the new raw packet. |
| Dependency facts | Baseline plus directed supporting paths, supported/excluded/unknown site counts and relationship status for each observation. |
| Measurement age | Baseline plus measurement time, report time, both ages, declared validity and current/stale/unknown status. |
| Both facts | Baseline plus the two independently calculated fact blocks. |

All variants retain the compact observations, service impact, topology and change record. An explicit field allowlist excludes answer keys and generation metadata. The calculators use raw input evidence without reading references or changing the packet.

### Dependency calculation

An edge `[site, component]` means the site depends on the component. The calculator follows that direction and exposes a supporting path for each affected site. A positive path can support a relationship in a partial map. An absent path excludes a relationship only when the map declares complete coverage of required service dependencies and the site and observed asset are known.

Missing topology, unknown edge semantics, an inconsistent affected-site count or an unresolved cycle prevents a negative conclusion. A supported relationship still does not prove a fault caused the service impact.

In **relay detour**, packet B redirects the final dependency edge away from the component reporting receive failures. The added summary changes from `all_listed_sites_depend` to `no_listed_sites_depend`. The raw alarm remains identical. Inspect both packets to see the exact path and edge that changed.

### Measurement calculation

In **roof supply display**, both reports arrive one minute before the decision. Packet A's voltage measurement is five minutes old; packet B's is 95 minutes old. The compact baseline discards measurement timestamps, so these two baseline requests are identical.

The measurement variant adds the distinction explicitly:

```json
{
  "observation_index": 0,
  "report_age_minutes": 1.0,
  "measurement_age_minutes": 95.0,
  "declared_valid_for_minutes": 15,
  "freshness_status": "stale"
}
```

The full block also includes the source timestamps and the provisional basis for validity. Missing measurement time produces `measurement_age_minutes: null` and `freshness_status: "unknown"`; it does not substitute report age. Impossible timestamp order and invalid windows fail validation.

Eight development pairs have identical baseline requests but different draft references because only measurement time changes. Their baseline cannot distinguish the two decisions. Adding the facts restores that information; it does not guarantee the classifier will use it correctly.

## Models and controls

Each of the four local classifiers fits on the same 72 new training packets. They use the experiment 2 recipe: word and character TF-IDF, structured impact features and four logistic regression heads. Priority uses impact features alone. Word/character vocabularies fit independently for each input variant, using the same settings. Development data does not enter fitting.

The new facts enter ML as text in the state string. This pilot does not add structured dependency or age features. That keeps the first comparison focused on input representation; a later feature comparison can test whether explicit numerical and categorical features work better.

Prepared Jev requests use `jev-1.13.0`, the unchanged policy and experiment 2 Choice definitions. Each corresponding ML variant receives exactly that request's state string. Jev's training history differs from these local classifiers. No hosted requests have been sent, so the page exposes prepared requests rather than fabricated Jev outcomes.

Rules retain the original keyword routing and impact-priority calculation. They do not use the new fact calculators.

## Local results

Run `development-2026-10-01-v2` scores the 36 development packets against provisional references. The [machine-readable report](../checkpoints/experiment-3-development-2026-10-01.json) records data and source fingerprints, training settings, saved prediction fingerprints and full metrics. The app recomputes saved scores and checks fingerprints before displaying a local run.

| Local approach | All four correct | Both packets correct | Owner | Next check | Evidence |
|---|---:|---:|---:|---:|---:|
| Compact baseline | 16.7% | 5.6% | 50.0% | 50.0% | 50.0% |
| Dependency facts | 30.6% | 11.1% | 50.0% | 61.1% | 52.8% |
| Measurement age | 13.9% | 0.0% | 50.0% | 47.2% | 50.0% |
| Both facts | 27.8% | 11.1% | 50.0% | 61.1% | 47.2% |
| Rules | 50.0% | 11.1% | 50.0% | 50.0% | 50.0% |

Priority is correct on every packet for all five approaches. All-four accuracy therefore equals the three-semantic-decision and software-priority scores here. “Both packets correct” requires all four decisions to match the accepted references on both members of a pair.

Dependency facts fix five baseline errors without losing a fully correct packet. Measurement facts fix two but introduce three regressions. Combining the facts fixes four baseline errors, but scores below dependency facts alone. Low pair accuracy means even the strongest local approach rarely gets both sides right.

The family breakdown gives useful starting points:

- **Inventory not delivered:** dependency facts raise fully correct packets from zero to two of four. Missing topology becomes an explicit unknown.
- **Feeder excerpt:** dependency facts raise correctness from three to four. Measurement facts reduce it to one, even though the measurements are current in both packets.
- **Archive edge append:** every ML variant misses all four packets; rules get all four right. The added dependency facts alone do not solve the diagnostic wording and disposition.
- **Roof supply display** and **resolver trace delay:** measurement facts fix one packet in each family, while combined facts get none fully correct. Inspect the separate owner, diagnostic and evidence outputs to see where the decisions disagree.

The added facts expose information that compact inputs lose, but text features and independently fitted heads still produce inconsistent decisions. This small pilot does not isolate the reason for every regression. It also does not establish that rules are generally better, that Jev will improve, or that the historical 96.8% revised-ML test score has fallen. These are different packets, training data and provisional references; historical score deltas would be misleading.

## Reproduce and inspect

Start the app and open `/experiment-3`. A fresh clone can inspect inputs and exact requests immediately. **Run local ML comparison** fits four local models and writes a new ignored run directory; it does not call Jev. Every run is separate and existing outputs cannot be overwritten.

The same workflow is available from the repository root:

```bash
uv run --locked python -m scripts.run_experiment3_local validate
uv run --locked python -m scripts.run_experiment3_local run --output runs/experiment-3/my-first-pilot
```

The tracked report describes the recorded pilot; per-packet predictions require the local run or a replay. The app does not present the report as live results when those predictions are missing.

## Next steps

I will review the cases and references with a network specialist before treating these scores as a basis for choosing a transformation. The first review should address dependency completeness, telemetry validity and conflicting evidence.

A bounded Jev development comparison would use the same four prepared inputs: 36 packets × four variants, or 144 hosted requests. It needs explicit run settings, request fingerprints and retained responses. The current page exports requests and runs local ML only.

For ML, the next controlled comparison can add structured relationship and freshness features while retaining this text baseline. Any revision should use further development cases, record regressions and keep training separate. Reviewed references, fixed transformations and questions must precede evaluation on new held-out families. Read-only diagnostic tools and raw KPI anomaly detection remain later work.
