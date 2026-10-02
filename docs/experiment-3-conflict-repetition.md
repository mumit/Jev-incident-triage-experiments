# Experiment 3: conflict repetition

October 2, 2026. This development check asks whether the remaining stale-conflict error recurs on further cases, and whether repeated identical requests change Jev's decisions. The [question-precedence trial](experiment-3-question-precedence.md) stays frozen. No input transformation or question revision is introduced here.

## Setup

Four new written families supply two independent instruments measuring the same quantity on the same component under comparable conditions: cabinet DC bus, load-panel DC output, optical receive power and radio clock offset. Packet A contains two current contradictory reports. In B, only the nominal reading's measurement timestamp changes from four to 83 minutes old. Both reports arrive one minute before the decision. One family places the nominal observation first to exercise indexing, but it is a separate written case, not an isolated order experiment.

The draft references retain NOC and gather evidence on A. B supports the current malfunction's domain and diagnostic. The user-selected NOC rule remains in effect. The 15-minute window, instrument classifications and conflict disposition remain teaching assumptions awaiting specialist review. These are constructed examples, not validated network thresholds or independent operational incidents.

Each of the eight distinct packets receives the same combined evidence and the same two question sets used in the preceding trial. The checkpoint, policy, choices and priority question are fixed. Three planned repetitions repeat each request exactly, for a maximum of **48 hosted calls**. This tests recurrence and response variation; it does not test an improvement.

## Recording and scoring

The master plan saves all 48 exact requests before the first call. Each repetition writes its own immutable run and eight-packet score set. Serial execution alternates arm order by packet, without warmup or automatic retries. If a repetition has a failed or unattempted response, later repetitions stop. Failed and missing responses remain in the planned denominator. Provider charges apply.

Report each repetition, each packet's choices across repeats, correct decisions, correct pairs and agreement of the four selected answers. Different returned probabilities alone do not count as changed decisions. Repeated responses are not additional independent cases: the study still has eight distinct packets and four correlated pairs. Three repeats do not establish general reproducibility or operational calibration.

## Results

Run `development-2026-10-02-v1` completed all 48 requests with zero failures. All responses reported `jev-1.13.0`. The [machine-readable report](../checkpoints/experiment-3-conflicts-2026-10-02.json) records the master request plan, each repetition and packet-level agreement. The app verifies the source, input and request fingerprints and recomputes each score before showing evidence.

| Question set | All four correct in repeats 1 / 2 / 3 | Both packets correct in each repeat | Correct responses across repeats | Packets with identical decisions |
|---|---:|---:|---:|---:|
| Original | 0.0% / 0.0% / 0.0% | 0/4 | 0/24 | 6/8 |
| Explicit precedence | 50.0% / 50.0% / 50.0% | 0/4 | 12/24 | 8/8 |

Priority is correct on every response. The explicit questions retain NOC, gather evidence and mark evidence insufficient on both sides of every pair. That matches all four current-conflict packets A, but misses all four packets B after the nominal measurement becomes stale. The failure recurs for power, transport and radio evidence, including the case with the nominal observation first.

The original questions choose the observed domain on both sides of each pair. That gets B's owner right but A's owner wrong. They mark evidence insufficient on every packet, so every B still fails. Two load-panel packets also change diagnostic choice across repetitions: A changes from a power diagnostic to gathering evidence; B changes from gathering evidence to a power diagnostic. Neither becomes fully correct.

Explicit precedence fixes the current-conflict owner on all four families, but **regresses the stale-conflict owner** from the domain to NOC on all four B packets in every repetition. Three identical wrong answers show agreement, not reliability.

### Interpretation

The remaining failure is more than a single unusual response: it recurs on these four new conflict patterns and all three repeats. The explicit questions improve handling of current conflicts while failing to use freshness to dismiss an old contradiction. These outputs do not reveal Jev's internal reason. Recent report arrival, the conflicting narrative or the fact representation are possible explanations; this trial does not isolate them.

The earlier 93.8% score came from a broader, different development pack. The 50.0% score here describes a targeted conflict subset, not a drop measured on the same cases. Eight packets and three serial repeats also cannot establish population accuracy, independence of responses or general model reproducibility.

The subsequent evidence-selection comparison retained raw reports for inspection and calculated which measurements were current and related. It separated an explicit eligibility summary from an input containing only eligible observations, with questions fixed and current-conflict controls retained. Further development families kept this design separate from the cases that informed it. Reference and validity-window review must precede final held-out evaluation. The subsequent [structured ML comparison](experiment-3-structured-ml.md) records the feature study and its remaining wording failures.

## Inspect

[Open the repeated conflict workbench](http://127.0.0.1:8768/experiment-3?trial=conflicts). **Repetition** switches the score set and selected response without changing the packet or question wording. **Decisions** also shows all three repetitions for the selected packet, with draft-reference markers only after reveal. **Across all three repetitions** distinguishes response counts from the eight distinct packets and shows whether the four chosen answers agree.

**Exact input** preserves the original and explicit questions. Each repetition's request matches the master plan. Raw evidence, the current/stale facts, saved responses and probabilities remain available. A fresh clone exposes missing runs explicitly; the tracked report does not invent per-packet predictions. No ML fitting occurs in this check.

## Reproduce

```bash
uv run --locked python -m scripts.run_experiment3_conflicts validate
uv run --locked python -m scripts.run_experiment3_conflicts preflight
uv run --locked python -m scripts.run_experiment3_conflicts run --output runs/experiment-3-conflicts/my-repeated-comparison
```

A key in the environment or ignored `.env` is needed for hosted inference. A new output directory is required; existing runs cannot be overwritten. No training or held-out data is added.

## Subsequent input comparison

The [evidence-selection comparison](experiment-3-evidence-selection.md) completed 36 calls on 12 further packets with explicit questions frozen. Adding eligibility facts alone fixes no complete packet. Selecting eligible observations fixes all three stale-conflict packets and retains nine correct controls, including current conflicts. The repetition study stays unchanged; the new score is a matched comparison on different cases.

The [selection-robustness check](experiment-3-selection-robustness.md) completed 48 calls on eight new packets, repeating both frozen inputs three times. Selected observations match all eight draft references in every repeat; combined facts match seven. Selection fixes one validity-boundary packet, repeated three times, and introduces no new wrong fields. Both inputs pass the partial-inventory, missing-inventory and multiple-domain controls and keep identical decisions across repeats. The multiple-domain reference remains provisional; agreement does not establish correctness or operational reliability.

The subsequent [training-wording study](experiment-3-wording.md) keeps the structured ML recipe fixed. Its negative matched result and new power-owner regressions motivate a separate observation-interpretation comparison; the recorded Jev questions and inputs remain unchanged.
