# Declaration consistency and NOC retention

## Purpose

I selected NOC retention when structured instrument metadata and an explicit prose domain declaration disagree. This study compares that rule with the frozen metadata policy on further synthetic development families. The operation reading remains separate from the domain dispute.

Both paths copy domain from the occurrence’s structured metadata and share the same actual reader prediction for `fault`, `normal` or `unknown`. The candidate adds a software check for disagreement between valid explicit enum declarations. No model question, training recipe or operation reading changes.

## Data and references

The pack contains 80 packets in 20 families, arranged as 40 pairs. Each packet has two report occurrences. Their 160 occurrences reuse 40 distinct texts; one response per text and reader feeds both policies. A family fixes the underlying evidence pattern. Two graph/impact variants within each family share text, so these are correlated observations rather than independent model calls.

Pairs change one structured declaration, function, timestamp or asset link. They cover conflicting declarations on fault and normal reports; missing and ambiguous fault metadata; stale or unlinked normal reports with conflicts; and clean function-comparability controls. Text and report annotations remain identical across each pair, even when the structured declaration changes. Metadata must therefore join by occurrence, rather than copying the first occurrence’s domain across all instances of a text.

Report domain annotations describe the explicit prose header. Packet references apply the selected NOC rule to the full input. Both were written before inference and remain provisional synthetic references. These examples do not establish how often declarations fail, whether instruments report truthfully, or how representative the patterns are of a real network. There is no final held-out set.

## What changes in the policy

For example, a current linked report states `Instrument domain: core`, while structured metadata supplies `ran`. Its operation still reads `fault`. The base software-domain path can assign RAN. The consistency guard retains NOC, requests further evidence and leaves the impact-derived priority unchanged.

A current normal report can also expose a declaration conflict on a fault-bearing asset, even when it measures another function. Stale reports and reports without a visible path to affected service cannot block ownership. Missing or ambiguous structured fault metadata already supplies `none` under the frozen base policy; this is a control, not an improvement credited to the new guard.

The parser reads only the explicit `Instrument domain:` enum header. Technical words do not determine a domain or fault. It compares two supplied claims, without deciding which is true. Duplicate, missing and ambiguous prose headers do not establish a valid competing enum. Metadata age, provenance and source authority require separate evidence; this study does not invent expiry rules for them.

## Readers and evaluation

Jev uses the exact recorded declared-domain request builder, including its unchanged focal operation-reading question. Original and broader ML classifiers retain their frozen training and fitting settings. Report rules remain unchanged. Structured metadata, policy facts and reference answers stay outside every interpreter request. The guard makes no extra Jev calls.

Both paths preserve actual reading probabilities. Copied domain values carry no invented model probabilities. Raw interpreter domain predictions remain visible and score against prose annotations, but neither policy uses that head. Reading failures remain failures under both paths.

Evaluation separates distinct-text domain and reading scores, full-packet matches, paired success, field regressions and wrong readings hidden by matching packet decisions. Reference-reading-fed policy checks diagnose the implementation; they are not model performance or an accuracy ceiling. Saved local vectors and fitted score margins explain classifier decisions.

## Recorded results

Preparation source: `ee12a91`. [Protocol](../checkpoints/declaration-trust-protocol-2026-10-02.json), [local evaluation](../checkpoints/declaration-trust-local-2026-10-02.json), [Jev evaluation](../checkpoints/declaration-trust-jev-2026-10-02.json).

| Frozen reader | Base packet matches | Guard packet matches | Base / guard pair matches | Correct operation readings |
|---|---|---|---|---|
| Jev · declared-domain question | 56/80 | 80/80 | 16/40 → 40/40 | 40/40 |
| ML · original wording | 40/80 | 40/80 | 0/40 → 0/40 | 0/40 |
| ML · broader wording | 40/80 | 40/80 | 0/40 → 0/40 | 0/40 |
| Report rules | 56/80 | 72/80 | 16/40 → 32/40 | 36/40 |

Jev completed 40 hosted calls without failures. Its unchanged readings let the guard fix 24 packets, with no packet losses or newly wrong fields. These are policy fixes under the selected synthetic rule, not an improvement in Jev’s reading ability. The guard excludes stale and disconnected conflicting reports as intended. Both reference-reading-fed diagnostics and model scores remain inspectable separately.

Both ML controls predict `unknown` for all 40 outcomes. Their 40 matching NOC packets conceal incorrect readings; the guard cannot recover missing fault interpretations. Report rules fix 16 packets without losses, but four fault texts receive `unknown`. Eight matching packets under the guard still conceal wrong operation readings.

The first recorded attribution reused a scorer that compared copied structured domains with prose annotations. That comparison falsely counts deliberate source differences as reader errors. A separate verified evaluation corrects attribution using raw interpreter outputs and scores operation readings alone as a second view. Packet scores, distinct-text scores and model responses were unaffected; the original run files remain unchanged. The linked evaluations and app use corrected attribution.

## Next boundary

Agreement does not establish truth: both declarations could be wrong together. This guard checks consistency on simple explicit headers; it cannot validate source authority or resolve ambiguous declarations. A useful next ML comparison would add separate training examples of these instrument-report formats, keeping this study frozen and scoring further development families. Confidence in telecom operation still requires specialist-reviewed references and representative data before final held-out evaluation.
