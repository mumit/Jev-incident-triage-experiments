# Experiment 3: structured ML features

October 2, 2026. This comparison tests whether dependency and freshness facts help a local classifier when they become features bound to each observation, rather than additional prose. Jev's questions and evidence-selection filter stay frozen. This comparison makes no hosted calls.

## Data and references

The new pack contains 96 training packets and 64 development packets, each across 16 disjoint families. Correlated variations form 48 training pairs and 32 development pairs. Family names and scenario prose differ from earlier packs; the shared pair templates, vocabulary and policy remain constructed teaching material. They do not establish representative network data.

Pairs vary required-service paths, measurement time, conflicting nominal readings, inventory availability or report arrival. Recovery and unexplained maintenance provide monitor and change-check examples. Development includes the one-second validity boundary and a visible path in partial inventory. These mechanisms overlap training by design; family separation does not make this an independent operational evaluation.

References were written before fitting and follow the user-selected NOC teaching rule. A current domain-specific fault needs a visible affected-service path; stale, unknown or conflicting evidence stays with NOC. The 15-minute inclusive window and comparable-instrument conflict rule remain provisional. No final held-out families exist.

## Matched comparison

All four arms receive the same compact text state, impact features, training packets, target decisions and logistic-regression settings. Priority uses only impact features. Each semantic head uses word and character TF-IDF plus impact, as in the earlier text baseline. Shared vocabularies fit only on training data.

| Arm | Added features |
|---|---|
| Text baseline | None. |
| Structured dependency | Observation counts by supported, excluded or unknown relationship; each observation's text enters its matching relationship channel. |
| Structured freshness | Observation counts by current, stale or unknown freshness; each observation's text enters its matching freshness channel. |
| Both structured features | Counts and observation text channels for the joint relationship/freshness category. |

The calculators read timestamps and declared required-service paths. A visible path takes precedence over unknown relationships for other sites under this teaching rule. They do not classify malfunctions or produce investigating teams. Every observation remains available, including stale and conflicting reports. Asset identifiers support path calculation but become the word `asset` in the added observation features. The unchanged compact baseline still contains inventory identifiers.

For example, a current power fault and a stale nominal power reading enter separate `supported/current` and `supported/stale` channels. Their words remain separate. A packet-level count of one current and one stale reading would lose that connection. The classifier learns weights for the words in each channel from training examples.

The settings remain word ngrams 1–2, character ngrams 3–5, minimum document frequency 2, sublinear term frequency and balanced logistic regression with C=2, maximum 2,000 iterations and random state 17. Each arm fits once, with no development tuning. More channels add dimensions and model capacity as well as facts; the comparison does not isolate those effects. The text baseline omits measurement time, so some freshness-changing pairs have identical baseline features. That limitation is part of this input comparison.

## Results

Run `development-2026-10-02-v1` completed the four local fits and scored all 64 development packets per arm. No Jev calls occurred. The [machine-readable report](../checkpoints/experiment-3-structured-ml-2026-10-02.json) records training settings, fingerprints, scores and matched fixes or regressions. All saved evidence verifies.

| Approach | All four correct | Both packets correct | Owner / next check / evidence correct |
|---|---|---|---|
| ML · Text baseline | 24/64 (37.5%) | 6/32 (18.8%) | 59.4% / 57.8% / 59.4% |
| ML · Structured dependency | 38/64 (59.4%) | 10/32 (31.3%) | 65.6% / 68.8% / 68.8% |
| ML · Structured freshness | 46/64 (71.9%) | 14/32 (43.8%) | 71.9% / 71.9% / 76.6% |
| ML · Both structured features | 52/64 (81.3%) | 20/32 (62.5%) | 81.3% / 82.8% / 84.4% |
| Rules | 34/64 (53.1%) | 4/32 (12.5%) | 59.4% / 53.1% / 59.4% |

Priority is correct throughout and uses identical impact-only features across ML arms.

| Added ML features | Complete packets fixed / lost | Newly wrong owner / next check / evidence fields |
|---|---|---|
| Dependency | 16 / 2 | 10 / 9 / 2 |
| Freshness | 26 / 4 | 12 / 15 / 3 |
| Both | 28 / 0 | 8 / 10 / 0 |

A field regression counts even when the baseline already failed another field. Losing no complete packets therefore does not mean introducing no errors. Both features together still miss 12 packets: six transport cases and six power cases. Current-fault investigation, rather than priority, remains the main failure.

### What the weights show

Case `NSM-0ad33f97023a-a` has a current transport receive-channel fault on a visible affected-service path. The combined classifier chooses NOC at 85.0%; its draft reference selects transport. NOC's log-odds margin over runner-up power is 2.592. The intercept contributes 3.065; the observation-channel features `test` and `test at` each add 0.203. Other features partly offset those contributions. The microscope exposes the complete margin and the saved nonzero vector.

All 24 training observations containing the standalone word “test” describe normal readings. The development transport-fault text also uses “test.” This is a vocabulary shortcut in the constructed data: the model assigns positive NOC weights to wording that can describe either a healthy or faulty reading. The weights show their contribution to this fitted comparison; they do not prove that changing those words alone would correct the decision.

Another case, `NSM-f930c94ac2e7-a`, exposes a field regression. The baseline gets power ownership and power inspection right but marks evidence insufficient. The combined classifier fixes some other cases while changing this packet to NOC and gather evidence. Reviewing only complete-packet scores would conceal those newly wrong fields.

### Interpretation

Binding observations to calculated categories improves agreement on this pack. It preserves which reading is current and whether the affected service depends on its component, information the baseline cannot infer reliably from serialized text. Dependency-only and freshness-only features also introduce complete-packet regressions. The combined representation still fails under unfamiliar fault wording and sometimes returns inconsistent owner, diagnostic and evidence decisions because the heads fit separately.

These results compare feature sets on identical new data. They are not deltas from the earlier 36-packet experiment or a ranking against Jev's different development packs. Shared templates, extra feature capacity and simplified diagnostic prose limit the conclusion. High fitted probabilities remain uncalibrated.

## Next step

The [training-wording comparison](experiment-3-wording.md) is complete on 80 new development packets. Counterbalancing “tests” and “diagnostics” weakens their method-word weights but scores 61/80 against 64/80 for matched coupled wording. It fixes one packet and loses four, with new owner, diagnostic and evidence errors. The original training bridge scores 65/80. The next study will separate report interpretation from policy application using new development families; the original combined candidate stays unchanged. Specialist review remains necessary before final held-out evaluation.

## Inspect and reproduce

[Open the workbench](http://127.0.0.1:8768/experiment-3?trial=structured). Follow **Raw evidence → Calculated facts → Exact input → Decisions**. Exact input shows the common text, added counts and observation channels. Saved runs also expose the nonzero fitted feature vector. The score microscope compares the selected class with its runner-up: intercept plus all feature contributions reconstructs the log probability ratio. These weights explain a fitted score, not physical causation; probabilities remain uncalibrated.

```bash
uv run --locked python -m scripts.run_experiment3_structured_ml validate
uv run --locked python -m scripts.run_experiment3_structured_ml run --output runs/experiment-3-structured-ml/my-feature-comparison
uv run --locked python -m scripts.run_experiment3_structured_ml verify --output runs/experiment-3-structured-ml/my-feature-comparison
```

Runs cannot be overwritten. Inputs, predictions, feature vectors, explanations and scores have fingerprints. Earlier data and recorded models remain unchanged. Specialist review must precede final held-out evaluation; raw KPI anomaly detection remains separate.
