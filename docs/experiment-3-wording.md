# Experiment 3: counterbalanced ML wording

October 2, 2026. This study tests a training-data shortcut found in the structured ML comparison: “test” appeared only in normal readings, although a test can also find a fault. The combined feature construction and logistic settings stay frozen. Jev makes no calls.

Counterbalancing weakens the method-word weights but reduces agreement with the new draft references. I will retain the original training candidate while investigating how the classifier interprets fault evidence.

## Data and controls

Each arm fits 96 packets from the same 16 training families used in the structured-feature study. Targets, topology, timestamps, service impact and report order remain identical. The new development pack contains 80 packets in 20 further families, forming 40 correlated pairs. Its prose and family names differ from earlier packs; mechanisms, templates and simplified vocabulary remain shared teaching constructs. This is not representative network data or a final held-out evaluation.

| Training arm | What changes |
|---|---|
| Original training wording | The previous 96 training inputs, unchanged. This bridges the new study to the recorded candidate. |
| Matched coupled wording | Normal reports use the plural “tests,” in the same grammatical frame as “diagnostics.” Fault reports retain “diagnostics.” The association between method and reading outcome stays intact. |
| Counterbalanced wording | Only “tests” and “diagnostics” nouns change from the coupled arm. Both methods describe healthy and faulty readings. |

The intervention covers twelve domain families. The four extra teaching families stay unchanged. Counts describe reports, including repeated reports across paired packets:

| Arm | Fault reports: tests / diagnostics | Normal reports: tests / diagnostics |
|---|---|---|
| Coupled | 0 / 72 | 24 / 0 |
| Counterbalanced | 36 / 36 | 12 / 12 |

Each controlled pair keeps the same method word, so its original dependency or timestamp intervention remains the only change between A and B. Balancing is exact across domains. Within each domain, fault counts are 8/10 or 10/8 and normal counts are 2/4 or 4/2. These small differences preserve complete pairs; the study does not remove every possible association between wording and domain. Normal domain readings occur in conflicting-report packets, not as isolated healthy-domain cases. The noun change does not broaden that coverage.

For a training power fault, the matched inputs differ only here:

```text
Coupled:        Independent power diagnostics at [asset] record failed equipment supply. Current service checks confirm impact.
Counterbalanced: Independent power tests at [asset] record failed equipment supply. Current service checks confirm impact.
```

Some normal power reports make the reverse substitution:

```text
Coupled:        Independent power tests at [asset] report normal equipment supply under the same conditions.
Counterbalanced: Independent power diagnostics at [asset] report normal equipment supply under the same conditions.
```

The `[asset]` placeholder stands for the unchanged packet identifier. This is an input-word intervention, not an extra reference answer or a calculated fault category.

Development pairs cover affected-service paths, stale or unknown measurement times, comparable current conflicts and stale nominal reports. Eight additional pairs swap only “tests” and “diagnostics,” with unchanged reference decisions. Missing and incomplete inventory, recovery and unexplained maintenance provide controls. References were written before fitting and follow the user-selected NOC teaching rule. The 15-minute inclusive window and conflict interpretation remain provisional; specialist review is pending.

## Matched setup

All three arms use the frozen **Both structured features** recipe: compact text, impact features, observation counts and text channels bound to dependency/freshness categories. Every observation remains available. The calculators use only declared paths and timestamps; they do not classify faults or select an investigating team.

Each arm fits its word and character vocabularies on its own training text, then fits the same four logistic heads once. The training targets and 96-packet count stay fixed. Word ngrams 1–2, character ngrams 3–5, minimum document frequency 2, sublinear term frequency, balanced classes, C=2, maximum 2,000 iterations and random state 17 match the earlier recipe. Priority uses identical impact-only features.

Every arm receives exactly the same development packets and prepared input bundles. Learned vocabulary, vector dimensions and weights can differ because training wording changes. Shared feature construction therefore does not imply identical fitted vectors. The complete protocol and source/data fingerprints were saved before fitting; this pack received no subsequent tuning.

## Results

Run `development-2026-10-02-v1` completed all three local fits. The [recorded report](../checkpoints/experiment-3-wording-2026-10-02.json) includes scores, fixes, field regressions, method-word weights and source fingerprints. Saved predictions, vectors and score margins verify.

| Approach | All four correct | Both packets correct | Owner / next check / evidence correct |
|---|---|---|---|
| ML · Original wording | 65/80 (81.3%) | 27/40 (67.5%) | 81.3% / 81.3% / 87.5% |
| ML · Coupled wording | 64/80 (80.0%) | 26/40 (65.0%) | 80.0% / 80.0% / 87.5% |
| ML · Counterbalanced wording | 61/80 (76.3%) | 25/40 (62.5%) | 76.3% / 85.0% / 80.0% |
| Rules | 42/80 (52.5%) | 8/40 (20.0%) | 57.5% / 52.5% / 57.5% |

Priority matches every draft reference and has identical ML probabilities across arms. The primary matched comparison is counterbalanced versus coupled. It fixes one complete packet and loses four previously correct packets, introducing four wrong owner fields, one wrong next-check field and eight wrong evidence-sufficiency fields. Field regressions also count on packets that already failed another decision.

| Control | Coupled correct | Counterbalanced correct |
|---|---|---|
| Service path | 13/16 | 12/16 |
| Measurement time | 13/16 | 12/16 |
| Current versus stale nominal report | 14/16 | 15/16 |
| Method synonym | 10/16 | 8/16 |
| Incomplete inventory | 4/4 | 4/4 |
| Missing inventory | 2/4 | 2/4 |
| Recovery | 4/4 | 4/4 |
| Maintenance scope | 4/4 | 4/4 |

The counterbalanced arm returns identical four-field decisions on seven of eight synonym pairs, up from four. Both packets are correct on only four pairs in either arm. Greater stability therefore includes stable errors, particularly transport and power faults.

### What changed in the weights

In the supported/current observation channel, the coupled model's coefficient for “tests” favors NOC over power by +0.635. Counterbalancing reduces it to −0.026. The “diagnostics” coefficient changes from −0.448 to −0.057. Both method words become close to neutral in this comparison.

These are coefficients, not packet contributions. Each contribution also depends on its TF-IDF value, and the final score includes many other features and an intercept. Refitting changes the vocabulary and all weights. The movement supports the intended reduction in the method-word association; it does not establish reliable understanding of fault evidence.

### A fix and a regression

In `NSW-834dfcc6be01-b`, a current supported power fault accompanies a stale nominal report. Counterbalancing changes ownership from NOC (52.3%) to power (73.5%) and corrects all four decisions. The corresponding current-conflict packet remains with NOC.

In `NSW-ebc3b6e65b9a-a`, a single current power fault has a visible service path. Coupled wording selects power (53.3%). Counterbalancing selects NOC (48.1%), marks evidence insufficient and still recommends power inspection. Its NOC-over-power log-odds margin is +0.097: the +2.925 intercept narrowly outweighs −2.828 from all input features combined. This exposes both a lost correct packet and disagreement between independently fitted heads. Four lost packets involve current power faults; transport faults remain difficult in both arms.

The original training bridge scores one packet better than the coupled arm, while introducing two newly wrong evidence fields on already-failed packets. Even the grammatical normalization has effects, which is why the counterbalanced comparison uses the matched coupled control. The new 80-packet scores are not deltas from the earlier 64-packet pack or a ranking against Jev's different data.

## Next step

I will keep the original combined candidate and test fault-reading interpretation separately from policy application. A small supervised observation classifier could distinguish fault, normal and unknown readings within each domain. Its training annotations must come from the written observation evidence, with references kept separate; software can then apply the existing dependency, freshness and conflict rules to those readings.

The next comparison needs new development families with varied fault descriptions, healthy readings containing fault-related words, negation and explicit uncertainty. A text-only observation classifier and a rules interpretation should receive the same reports before either feeds the fixed policy. This would isolate whether the failure comes from reading a report or applying the decision rule. It would also create a new architecture comparison, so its scores must remain separate from this fixed-feature study. Specialist review still precedes final held-out evaluation.

## Inspect and reproduce

[Open the training-wording workbench](http://127.0.0.1:8768/experiment-3?trial=wording). **Training → Exact input** compares the actual original, coupled and counterbalanced reports. **Development → Decisions** shows predictions, fitted probabilities and score margins. The result view includes control scores, synonym agreement, method-word weights and links to the fix and regression above.

```bash
uv run --locked python -m scripts.run_experiment3_wording validate
uv run --locked python -m scripts.run_experiment3_wording run --output runs/experiment-3-wording/my-wording-comparison
uv run --locked python -m scripts.run_experiment3_wording verify --output runs/experiment-3-wording/my-wording-comparison
```

Runs are immutable. Raw evidence remains under ignored `runs/experiment-3-wording/`; the historical public bundle stays unchanged. A fresh clone can inspect training inputs and replay this local comparison without a Jev key. No model in this lab executes network changes.
