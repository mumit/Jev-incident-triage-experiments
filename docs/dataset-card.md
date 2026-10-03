# Dataset card: version 0.1.0

## Origin and use

I constructed this synthetic dataset for the fictional Northstar Telecom operator, using AI assistance to write scenarios and reference decisions. The dataset contains no private tickets, infrastructure inventory or operator procedures. Deterministic Python expands each regular scenario into 20 variations. “Authored” means written for this study, not drawn from real incident records. No domain specialist has certified the labels.

Use this release to develop adapters, test scoring, inspect failure modes, and pilot supervised training. Do not treat results as an estimate of real incident prevalence, production confidence calibration, or operational savings.

## Contents

There are 600 training, 220 validation, 220 test, and 24 challenge records. The regular sets comprise 30, 11 and 11 written scenario families respectively, with 20 realizations per family. Challenge records comprise 12 pairs across four intervention archetypes. A family is one scenario and its generated variations. Those variations are correlated. The 11-packet learning set contains the first validation packet from each family; it is a teaching subset, not a fifth split.

Each split has separate `.inputs.jsonl` and `.labels.jsonl` files. Inputs contain only an opaque ID, policy version and incident packet. Keys contain labels, accepted answers, rationales, generation metadata, and family identifiers. `manifest.json` records distributions and SHA-256 checksums.

Labels are `initial_owner`, `priority`, `next_check`, and `insufficient_evidence`. The current release uses one accepted answer per field. The evaluator supports multiple accepted decisions for correctness; probability scoring is skipped for fields with multiple accepted answers rather than inventing a target distribution.

## Construction and separation

The written evidence scenario determines the initial investigating domain and diagnostic action. A fictional policy determines priority from visible service impact. Cases lacking sufficient domain evidence explicitly remain with operations. None labels a confirmed physical root cause.

Scenario families are assigned to splits before realization. No family crosses splits. Topology IDs are disjoint and the common aggregation skeleton differs by split. Some independent-path graph shapes and policy language necessarily recur; this is not a guarantee of complete structural or semantic novelty. Realizations within a family share prose. Opaque IDs are excluded from model requests.

The priority task deliberately tests policy application to structured fields. A deterministic rule can solve it perfectly. It is not evidence that an AI model can independently infer customer impact.

Observations are narrative evidence summaries with occasional numeric measurements, not a physical simulation or complete raw telemetry. `observed_at` represents when the report is available; the prose may explicitly describe an older measurement. Topology excerpts are illustrative and may omit unaffected network elements. Synthetic observations can still contain technical simplifications or errors.

## Challenge interventions

- Change affected outage sites from nine to ten: priority must cross the policy boundary.
- Replace current power evidence with stale evidence: retain operations and gather fresh evidence.
- Add an irrelevant change-timing observation after independently verified recovery: disposition should remain monitoring.
- Remove all dependencies on an alarmed uplink: its alarm no longer justifies assigning the affected sites to transport.

Only the specified input field changes within each pair; IDs differ for scoring. No challenge archetype is used in training exports.

## Checks and limitations

The validator checks IDs, input/label correspondence, split-family separation, duplicate packets, timestamp availability, enum values, priority consistency, domain/action compatibility, pair-label relationships, and file checksums. These checks do not replace semantic review of the authored evidence.

Metrics include family-grouped bootstrap intervals, but 11 test families and four challenge archetypes are too few for strong generalization claims. The keyword baseline's high score indicates that much of this first release is straightforward. Larger independently written cases, realistic noisy notes, alternative diagnoses, and specialist review should precede model selection for operational use.

The runnable validator checks the public input records and answer-key rows. See `triage_bench/validate.py` for the implemented checks.

## Inspection and evaluation

The app joins inputs and keys for human inspection while keeping the keys out of inference. Original ML and Jev receive the same original state; revised ML and focused Jev receive the same compact state. Only ML fits on the 600 training packets. Five test and four challenge packets appeared in earlier runs, as disclosed in [the overview](experiment-overview.md).

Use [the data atlas](observatory.md) to inspect families and pairs, and [the evaluation plan](evaluation-plan.md) for score definitions. Raw KPI detection requires a separate dataset and experiment.

## Experiment 3 draft pack

The historical counts and definitions above remain unchanged. A separate `data/experiment-3-draft/` pack adds 72 training packets across 12 families and 36 development packets across nine disjoint families. Every pair changes one declared field. References remain provisional, and no new final held-out split exists. [The development guide](experiment-3-development.md#new-data) describes construction and review questions. Neither pack establishes real network representativeness.

## Question-precedence development pack

The subsequent `data/experiment-3-question-draft/` pack contains 16 further development packets in eight pairs across eight new written families. Six pairs change a draft decision; two test invariance. It has no training or held-out split. Both Jev arms receive identical combined evidence and differ only in three question instructions.

The references apply the user-selected teaching rule: keep NOC until current evidence links a fault to an affected service. The 15-minute window, conflict disposition and network realism remain unreviewed assumptions. The [question comparison](experiment-3-question-precedence.md) records exact changes and results. These families are now exposed development cases; later revisions need further cases.

## Conflict repetition pack

`data/experiment-3-conflict-draft/` adds eight development packets in four new written families. Each pair changes only the nominal measurement timestamp from current to stale. Three hosted repetitions do not create new incidents or independent families. The references, 15-minute window and instrument classifications remain unreviewed teaching assumptions. [The repetition guide](experiment-3-conflict-repetition.md) records the controls and results.

## Evidence-selection development pack

`data/experiment-3-selection-draft/` contains 12 packets in six new written families and decision-changing pairs. Three current-conflict controls pair with a stale nominal measurement; other pairs vary stale or unknown fault times or an excluded dependency relationship. The pack has no training or held-out split. References precede inference and remain provisional. [The selection guide](experiment-3-evidence-selection.md) explains filtering, source indices and the limits of these constructed instrument readings.

## Selection-robustness development pack

`data/experiment-3-robustness-draft/` contains eight packets in four new written families and correlated pairs: three decision changes and one invariance. They test an inclusive validity boundary, a visible path with partial inventory, missing inventory and concurrent current faults in two domains. References were written before inference; the multiple-domain disposition interprets the frozen no-unique-domain clause provisionally. Three repeated requests do not add independent incidents. The pack has no training or held-out split. [The robustness guide](experiment-3-selection-robustness.md) records the controls and measured results.

## Structured ML development pack

`data/experiment-3-structured-ml-draft/` contains 96 training packets in 16 families and 64 development packets in 16 further families. Forty-eight training pairs and 32 development pairs share constructed mechanisms and templates; the development pairs include 26 decision changes and six invariances. New prose and family names avoid overlap with earlier packs, but vocabulary correlations remain. In particular, training uses “test” only for nominal readings while development also uses it for a transport fault. References remain drafts and the pack has no final held-out split. [The feature guide](experiment-3-structured-ml.md) explains the measured transfer failures.

## Training-wording pack

The [wording study](experiment-3-wording.md) reuses the 96 structured-study training packets and their targets in three matched wording arms. Its 80 development packets form 40 pairs in 20 new families. Only method nouns differ between coupled and counterbalanced training inputs. New development references remain drafts, with no final held-out split. Shared templates, mechanisms and simplified vocabulary still limit independence and realism.

## Report-interpretation pack

The [report-policy study](experiment-3-interpretation.md) adds 186 training packets in 31 families and 108 development packets in 27 further families. Separate annotations describe the 210 training and 124 development reports as domain plus fault, normal or unknown. A stale or disconnected fault retains its fault annotation even when the packet reference retains NOC. These report meanings are written from the templates before fitting, not inferred from packet answers. Development pairs vary paths, measurement time, contradictions, negation, uncertainty and missing inventory. Domain names appear literally in report prefixes; shared templates and vocabulary make this a limited teaching pack. References, validity thresholds and same-asset comparability remain provisional. There is no final held-out split.


## Matched report-language pack

`data/report-language-draft/` contains original and broader training variants of the same 186 packets, 31 families and 210 separate report annotations. Only report detail changes; identifiers, method nouns, targets and non-text evidence remain matched. The original variant preserves the previous report-policy training inputs exactly.

Both arms receive the same 140 development packets, 35 new families, 70 pairs and 156 report annotations. These written cases extend path, currentness, conflict, negation, uncertainty and clause-scope mechanisms. Families and pairs share templates; 140 packets are not 140 independent real incidents. Explicit domain prefixes simplify classification. Focal clause meanings, core acceptance as a normal handler reading, 15-minute validity and comparable instruments remain draft assumptions.

The [study guide](report-language.md) records actual local and hosted results. Its diagnostic replay selects four inspected report texts and repeats their exact requests; it adds no new families or independent evaluation examples. [The reference decision](report-language-review.md) selects normal handler reading; earlier annotations remain unchanged. No final held-out set exists.

## Measured-function pack

`data/report-scope-draft/` contains 68 development packets, 88 report annotations written separately from packet references, 17 further families and 34 single-field pairs. Eight core patterns and nine transport/RAN/power patterns separate intake, completion, expected rejection, malfunction and uncertainty. Shared templates, explicit domain prefixes and declared measurement scopes limit realism. Two predeclared packets expose the fixed policy’s inability to distinguish functions on one asset. Frozen ML training remains in the previous pack; no new annotations enter fitting. [The guide](report-scope.md) records the complete protocol and results.

## October 2 instrument metadata comparison

The [metadata policy study](metadata-policy.md) holds each interpreter’s readings fixed across asset and metadata grouping on 48 new development packets. Both Jev question controls improve 26/48 → 40/48, fixing 14 packets without losses. Frozen original and broader ML stay at 24/48; report rules improve 24/48 → 30/48. Sixteen distinct report texts supply 96 correlated occurrences; only 32 Jev calls were made. Metadata enters policy alone, with conservative handling of unresolved relevant scope.

Inspect **Comparison → Instrument metadata policy** at `/metadata-policy` for raw scope, both policy traces, exact requests, returned meanings and ML score contributions. References remain drafts. The [recorded domain choice](metadata-domain-review.md) identifies the declared instrument source, with service relevance checked separately by policy. These later raw runs are outside the historical public bundle.

## October 2 declared-domain comparison

The [declared-domain pack](declared-domain.md) contains 64 development packets, 128 report occurrences, 16 new families, 32 pairs and 30 distinct normalized texts. Families cover generic outcomes, technical distractions, missing or ambiguous declarations, stale faults and disconnected faults. Prose and structured declarations agree by construction; no contradictory declarations or trustworthy real instrumentation are demonstrated. Report and packet references remain separate prewritten drafts.

The [next trust choice](declaration-trust-review.md) concerns contradictory structured and prose declarations. Specialist review and held-out evaluation remain pending.
