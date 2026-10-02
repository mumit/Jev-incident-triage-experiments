# Experiment 3: selection robustness

October 2, 2026. The [evidence-selection comparison](experiment-3-evidence-selection.md) fixed three stale-conflict packets and retained nine controls. This check keeps the filter, explicit questions and Jev checkpoint unchanged on further development cases, with repeated identical requests.

## Cases and references

Four new written families supply eight packets in four correlated pairs. They share the study's constructed vocabulary and teaching assumptions. No training or final held-out set is added. References were written before inference and remain provisional.

| Pair | Controlled change | Draft decision |
|---|---|---|
| Optical validity boundary | Nominal measurement age changes from exactly 15 minutes to 15 minutes and one second; the fault stays current. | Both measurements conflict in A. The stale nominal report cannot contradict the current transport fault in B. |
| Partial radio branch visibility | Inventory coverage changes from partial to complete, with the same visible path from one affected site. | Investigate radio in both. The frozen questions require at least one visible path; the partial map cannot prove absence for the other site. |
| Missing feeder inventory | Missing inventory becomes a supplied required-service map. | Retain NOC in A; investigate power in B. |
| Concurrent supply and forwarding faults | The transport fault's measurement becomes stale; the related power fault stays current. | A has two supported domains. The frozen questions' no-unique-domain clause supplies a provisional NOC reference. B supports only power. |

The boundary is inclusive in the existing calculator. Its 15-minute window is a teaching assumption, not a validated optical threshold. The multiple-domain disposition needs specialist review: current relationships alone do not identify which team should investigate first, and the questions do not specify investigation sequencing. A disagreement there may reveal a policy ambiguity. It must not trigger a post-run reference change.

## Comparison

**Combined facts** retains every observation plus dependency and age facts. **Eligible observations only** uses the unchanged `selection.py` filter. Eligibility requires a current measurement and at least one visible affected-service dependency path. Unknown freshness or unsupported relationships cannot pass. It neither classifies malfunction nor selects a fault domain.

Filtering must retain both current contradictory measurements and both current domain faults. Missing inventory produces an empty eligible set. The partial inventory control preserves the observation because a path remains visible. Raw reports stay inspectable outside filtered requests, and retained rows preserve source indices while their request indices join consistently.

Both inputs use the frozen explicit questions and `jev-1.13.0`. Three planned repetitions repeat each exact request, for **48 calls**. Arm order rotates by packet within each repetition. All requests are saved before the first call; no warmup, tuning or automatic retries occur. A failed or incomplete repetition stops later repetitions. Failed and missing responses remain in the planned denominator.

Report each repeat, complete-packet and field fixes or regressions, pair correctness and agreement of the four selected answers. Eight distinct packets are still eight packets; the repeated responses are not additional independent incidents. Neither agreement nor a high score establishes operational reliability.

## Results

Run `development-2026-10-02-v1` completed all 48 requests with zero failures. Every response reported `jev-1.13.0`. The [machine-readable report](../checkpoints/experiment-3-robustness-2026-10-02.json) records the master plan, per-repeat scores and packet-level agreement. The app verifies source, input, request and response fingerprints and recomputes the scores before showing results.

| Input | Correct packets in repeats 1 / 2 / 3 | Correct pairs in each repeat | Correct responses across repeats | Packets with identical decisions |
|---|---|---|---|---|
| Combined facts | 7/8 / 7/8 / 7/8 | 3/4 | 21/24 | 8/8 |
| Eligible observations only | 8/8 / 8/8 / 8/8 | 4/4 | 24/24 | 8/8 |

Priority is correct in all responses. The combined input repeats the boundary B error: it retains NOC, gather evidence and evidence insufficient after the nominal reading becomes stale by one second. Selection fixes all three decisions in every repeat. It retains the other seven correct packets and introduces no newly wrong fields. The gain is one distinct packet, repeated three times, not three independent fixes.

Both inputs keep NOC on the current-conflict boundary A packet. They investigate radio with a visible path in either partial or complete inventory, retain NOC when inventory is missing, and select power after the map is supplied. Both also match the provisional multiple-domain references: NOC with two current supported domains; power after the transport measurement becomes stale.

### Interpretation

The unchanged filter passes these additional controls, and its boundary gain persists across three back-to-back repeats. Both inputs also show complete agreement of their four selected answers. That includes the combined input's repeated error, so agreement remains separate from correctness. These serial repeats do not establish stability across time, deployments or model versions.

The missing-inventory and partial-path cases add no measured filtering gain because the combined baseline already passes them. The multiple-domain result is agreement with a provisional interpretation, not evidence that NOC is the correct operational first owner. Specialist review still needs to settle sequencing, validity windows and inventory semantics.

Eight constructed packets cannot establish safe context removal or representative network accuracy. Their vocabulary, required-path graphs and independent instrument reports simplify real telemetry. One-second freshness classification is exact software behavior under a declared window; it does not validate that window. The earlier 12/12 selection result uses different cases, so this is a further check rather than a score delta.

## Next step

The [structured ML comparison](experiment-3-structured-ml.md) fits four matched classifiers on 96 new training packets and scores 64 development packets. Both feature blocks together match 52/64 draft references versus 24/64 for the text baseline, with 20/32 versus 6/32 pairs correct. It fixes 28 complete packets and loses none, but introduces eight wrong owner fields and ten wrong diagnostic fields on already-failed packets. Current transport faults still receive NOC at about 85% probability. Jev makes no calls in this comparison.

The next development study will counterbalance fault and nominal wording while keeping feature construction and classifier settings fixed. Training uses “test” only in nominal readings; development also uses it for transport faults. New development families must check whether broader wording reduces that shortcut without losing freshness and dependency behavior. Specialist review remains necessary before final held-out evaluation.

## Inspect and reproduce

[Open the workbench](http://127.0.0.1:8768/experiment-3?trial=robustness). **Repetition** selects a score set and saved response. **Calculated facts** explains eligibility and source-to-request indexing. **Exact input** preserves the fixed questions and both states. **Decisions** shows all three repetitions for the packet; draft-reference markers appear only after reveal. A fresh clone exposes missing results explicitly.

```bash
uv run --locked python -m scripts.run_experiment3_robustness validate
uv run --locked python -m scripts.run_experiment3_robustness preflight
uv run --locked python -m scripts.run_experiment3_robustness run --output runs/experiment-3-robustness/my-repeated-check
```

A server-side key is required for hosted inference; provider charges apply. Runs cannot be overwritten. All earlier datasets, requests and responses stay frozen. Raw KPI anomaly detection remains separate.
