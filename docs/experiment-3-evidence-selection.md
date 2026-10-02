# Experiment 3: evidence selection

October 2, 2026. The [conflict repetition](experiment-3-conflict-repetition.md) found that explicit questions repeatedly treated a stale nominal measurement as a current contradiction. This comparison tests whether software-calculated eligibility or observation selection helps Jev apply the same questions.

## Setup

Six further written development families supply 12 packets in six pairs. Three pairs contain independent comparable measurements of rectifier voltage, optical receive power or radio phase. A contains a current malfunction and a contradictory current nominal reading. In B, only the nominal measurement timestamp changes from five to 91 minutes old. Both reports arrive one minute before the decision. The radio pair places the nominal report first to check source-index preservation.

The other pairs change a fault measurement from stale to current, unknown to current, or excluded by the dependency map to related. Their A packets retain NOC; B supports the malfunction's domain. These controls check whether filtering removes useful current contradictions and whether an empty eligible set still retains NOC. All reference decisions were written before inference.

The families and packet IDs differ from the earlier development packs. They still share constructed vocabulary and assumptions. The 15-minute window, instrument classifications and conflict disposition remain provisional. These are teaching examples, not validated network thresholds, operational incidents or held-out evaluation.

## Three inputs

| Input | What Jev receives |
|---|---|
| Combined facts | All reports plus the existing dependency paths and measurement-age facts. This matches the preceding trial's explicit-question input construction. |
| Eligibility facts | The combined input plus an explicit current-and-related flag and exclusion reasons for each observation. All reports remain. |
| Eligible observations only | The eligibility input with ineligible observations and their associated fact rows removed. Retained rows receive consistent new indices and preserve their original source indices. |

Eligibility requires a measurement within its declared validity window and at least one visible required-service dependency path from a listed affected site. Missing measurement time or validity stays unknown and cannot pass. A partial map can support a visible path; it cannot prove absence. An excluded or unsupported observation does not pass.

The calculator does not interpret the observation as faulty or nominal, assign a domain, compare readings or produce a decision. Two current related measurements remain eligible even when they contradict. If none pass, the selected input contains empty observation and fact arrays, plus the original service impact, change record, topology and eligibility counts. The app retains all raw reports outside that request.

### Inspect a transformation

For the radio pair's B packet, raw observation 1 is the stale nominal reading and raw observation 2 is the current timing fault. The combined input retains both. The eligibility input marks observation 1 ineligible with `measurement_stale`, while retaining its narrative. The selected input removes that narrative and its dependency and age rows. The remaining observation becomes index 0 in every array and retains `source_observation_index=1`, referring to the second raw report.

This comparison separates adding an eligibility summary from selecting observations. Selection also changes request length, array positions and which fact rows remain. A gain would support this input construction on these cases; it would not isolate token count, prove Jev's internal reasoning or validate filtering for operations. Filtering can remove relevant context when timestamps or inventory are wrong.

## Controls and recording

All three inputs use the unchanged explicit questions from `question_trial.py`, the same policy, answer choices, priority rule and `jev-1.13.0` checkpoint. No ML fitting occurs. Each packet receives one call per input, for a maximum of **36 requests**. Arm order rotates by packet; no warmup or automatic retries occur. One response per arm does not measure variability.

The run saves all exact requests, data, references and source fingerprints before its first call. Failed and missing responses remain in the planned denominator. Saved responses, probabilities, request hashes and recomputed scores support inspection. Provider charges apply. The historical runs and frozen questions remain unchanged.

## Results

Run `development-2026-10-02-v1` completed all 36 requests with zero failures. Every response reported `jev-1.13.0`. The [machine-readable report](../checkpoints/experiment-3-selection-2026-10-02.json) records fingerprints and scores. The app verifies the exact requests and response-file hashes and recomputes each score before displaying results.

| Input | All four correct | Both packets correct | Owner / next check / evidence correct |
|---|---:|---:|---:|
| Combined facts | 9/12 (75.0%) | 3/6 | 75.0% / 75.0% / 75.0% |
| Eligibility facts | 9/12 (75.0%) | 3/6 | 83.3% / 75.0% / 91.7% |
| Eligible observations only | 12/12 (100.0%) | 6/6 | 100.0% / 100.0% / 100.0% |

Priority is correct in every response. The combined input repeats the stale-conflict error on all three B packets: NOC, gather evidence and evidence insufficient despite a current related malfunction. All nine other packets are correct, including the three current-conflict controls and the three A packets whose fault is stale, undated or unrelated.

Adding eligibility facts fixes the optical B packet's owner and evidence-sufficiency answers, and the radio B packet's evidence-sufficiency answer. Their diagnostics still gather evidence, and radio's owner stays NOC. The rectifier B packet remains unchanged. No complete packet improves, and no previously correct field becomes wrong. These partially improved outputs also expose inconsistent decisions within a packet.

Selecting eligible observations fixes all three B packets. It retains the nine correct packets, including every current conflict and empty-evidence control. All six pairs become fully correct. Relative to the matched combined baseline, that is three packet fixes, no complete-packet regressions and no newly wrong fields.

### Interpretation and next step

This result supports testing the selected input further. An explicit eligibility summary alone did not resolve the remaining conflicts, while removing the ineligible narrative and associated facts did. The radio case also passed after the retained observation moved from raw position 2 to request position 1. The calculator supplied evidence eligibility, not a fault domain or reference answer.

Twelve constructed packets and one response per arm do not establish general reliability. The 100% score is agreement with provisional references on this pack. Different request lengths, positions and fact rows changed together. The earlier 50% repetition score used different cases; it is not the baseline for this gain.

Before expanding the filter, I will test it unchanged on further development cases that could expose information loss: validity-window boundaries, partial inventory with a visible path, missing inventory, and multiple current fault reports. Repeated fixed requests can check whether the gain persists. Specialist review must settle the policy and telemetry windows before a final held-out evaluation. Structured-feature ML and raw KPI anomaly detection remain separate tasks.

## Inspect and reproduce

[Open the workbench](http://127.0.0.1:8768/experiment-3?trial=selection). Select **Evidence input** and follow **Raw evidence → Calculated facts → Exact input → Decisions**. The eligibility table maps each raw observation to its request position or marks it removed. References stay separate and hidden until revealed. A fresh clone shows missing hosted results explicitly.

```bash
uv run --locked python -m scripts.run_experiment3_selection validate
uv run --locked python -m scripts.run_experiment3_selection preflight
uv run --locked python -m scripts.run_experiment3_selection run --output runs/experiment-3-selection/my-input-comparison
```

A server-side key is needed for inference. Existing run directories cannot be overwritten. No new training or held-out data is added. Reference review remains necessary before final evaluation; the separate structured-feature ML comparison is pending.
