# Instrument metadata and policy grouping

## Question and controls

I selected **explicit instrument metadata first** on October 2, 2026. This comparison tests policy grouping while holding each interpreter’s predicted report meanings fixed. It keeps all earlier questions, models, data, references and results intact.

The original policy groups eligible readings by domain and asset. The candidate adds the measured function and a declared comparison context. A fault and a normal reading conflict only when all four identifiers match. A relevant eligible report with missing, ambiguous or incomplete scope retains NOC. Reports that are stale or outside the affected-service path cannot create a scope block.

Distinct declared contexts represent known different measurement conditions. For example, an operation can fail under one load condition and succeed under another. A successful reading under the second condition does not refute the observed fault under the first. Unknown conditions remain unresolved. These are provisional synthetic definitions, not reviewed operational policy.

Priority, report interpretation, freshness, topology eligibility and the diagnostic action mapping remain unchanged. The comparison changes grouping **and** conservative handling of unresolved scope; it cannot isolate the contribution of those two changes separately.

## Supplied metadata

A report might carry:

```json
{
  "measurement_scope": {
    "status": "declared",
    "function": "request_intake",
    "comparison_context": "condition-A"
  }
}
```

A second report can identify `registration_completion` on the same asset. Success at intake and failure at completion can coexist. If both reports instead describe registration completion under `condition-A`, their normal/fault readings contradict each other.

The metadata identifies what an instrument measures and the conditions under which readings can be compared. It contains neither a fault status nor a reference decision. `declared` means the synthetic input supplies that scope; it does not verify a real instrumentation schema, data lineage or trust mechanism. Missing scope appears as a null or absent field. An ambiguous scope carries `status: ambiguous`; its other fields cannot establish comparability.

Only policy receives these fields. Jev and ML still receive normalized report text alone. Their fixed question instructions and training recipes remain unchanged. Report text describes the outcome of the monitored operation without naming its function, so changing function metadata does not contradict a function named in prose. This deliberately controlled boundary is simpler than real telemetry.

## New data and response reuse

The pack contains **48 development packets, 96 report occurrences, 12 new families and 24 pairs**. Each family has two correlated graph/impact variants, covering one or 12 affected sites. All records describe degraded service, producing P3 or P2 through the existing impact policy.

Eight families change either function or comparison context across core, transport, RAN and power. Four further families cover missing scope, ambiguous scope, stale missing-scope evidence and unlinked missing-scope evidence. Each pair changes one declared metadata or eligibility field. Its report texts and separately prewritten domain/reading annotations remain identical.

These 96 report occurrences contain **16 distinct normalized texts**. Each Jev reader makes one call per distinct text, for **32 calls in total**. The saved response joins every occurrence of that text, including both packets in a pair. Both policies therefore receive identical meanings without paying for duplicate calls or introducing sampling differences between paired inputs. Occurrence scores and packet scores are correlated; they are not 96 independent model observations.

Jev’s original and measured-function questions remain separate frozen controls. Original-phrase ML, broader-phrase ML and report rules also feed both policies. Both ML models reuse their earlier 210-report training recipes, without new fitting labels or development tuning. The candidate policy does not become a new interpreter or use report annotations during inference.

Explicit domain prefixes, written operation outcomes, supplied metadata and shared templates limit realism. References were written before inference, separately for reports and packet decisions. All remain drafts; no final held-out set exists.

## Preflight diagnostic

Feeding the prewritten report meanings to the original policy matches **28/48** packet references. Feeding them to the metadata candidate matches **48/48**, fixing 20 packets. This diagnostic was recorded before model calls. It verifies the intended synthetic policy intervention; it is neither model performance nor an accuracy ceiling. Incorrect readings can still hide a policy error or produce a matching decision for the wrong reason.

The [prepared protocol](../checkpoints/metadata-policy-protocol-2026-10-02.json) records source/data fingerprints, both frozen Jev question sets, deduplicated request counts and diagnostic disagreements. The plan sends 32 serial requests, alternating reader order by text. It saves all requests and occurrence joins before the first call, makes no warmup calls and does not retry automatically. Access, configuration, rate-limit, model-checkpoint and network errors stop the run. Three consecutive malformed replies also stop it. A failed or missing shared response invalidates every dependent packet prediction in both policies.

## Running and preserving evidence

```sh
.venv/bin/python -m scripts.run_metadata_policy validate
.venv/bin/python -m scripts.run_metadata_policy preflight
.venv/bin/python -m scripts.run_metadata_policy local --output runs/metadata-policy/development-2026-10-02-v1
.venv/bin/python -m scripts.run_metadata_policy hosted --output runs/metadata-policy-jev/development-2026-10-02-v1
.venv/bin/python -m scripts.run_metadata_policy verify --output runs/metadata-policy/development-2026-10-02-v1
.venv/bin/python -m scripts.run_metadata_policy verify --output runs/metadata-policy-jev/development-2026-10-02-v1
```

New run directories refuse overwrites and remain ignored. Local evidence includes actual predictions, 32 distinct-text ML vectors and 64 fitted score margins. Hosted evidence includes exact requests, returned choices, distributions, latency and occurrence mappings. The historic public release remains unchanged. A fresh clone can rerun local controls; new hosted inference needs a server-side key and incurs charges.

## Results

All **32 hosted requests completed without failures** from frozen preparation commit `9904290`. Both Jev question controls produce identical domain/reading choices on this pack, although their returned probabilities differ. Each control’s actual predictions remain identical across its two policy arms. The [Jev checkpoint](../checkpoints/metadata-policy-jev-2026-10-02.json) and [local checkpoint](../checkpoints/metadata-policy-local-2026-10-02.json) retain matched changes, field regressions, interpretation scores and evidence fingerprints.

| Frozen reader | Asset policy: packets match | Metadata policy: packets match | Metadata policy: complete pairs match | Packets fixed / lost |
|---|---:|---:|---:|---:|
| Jev · original report question | 26/48 | 40/48 | 16/24 | 14 / 0 |
| Jev · measured-function question | 26/48 | 40/48 | 16/24 | 14 / 0 |
| Report ML · original phrases | 24/48 | 24/48 | 0/24 | 0 / 0 |
| Report ML · broader phrases | 24/48 | 24/48 | 0/24 | 0 / 0 |
| Report rules → policy | 24/48 | 30/48 | 6/24 | 6 / 0 |

No policy comparison introduces a newly wrong owner, priority, diagnostic or evidence field. These improvements measure agreement with the prewritten draft references on a controlled metadata intervention. They do not establish operational performance or metadata reliability.

### Interpretation limits

| Reader | Domain matches: distinct texts | Reading matches: distinct texts | Both match: distinct texts |
|---|---:|---:|---:|
| Both Jev question controls, separately | 11/16 | 16/16 | 11/16 |
| Report ML · original phrases | 1/16 | 0/16 | 0/16 |
| Report ML · broader phrases | 16/16 | 8/16 | 8/16 |
| Report rules | 12/16 | 8/16 | 6/16 |

Jev returns fault/normal in agreement with every operation-outcome annotation. Five domain readings disagree with their draft annotations: all four RAN texts and one power fault text receive none in both controls. Those five texts occur in 28 report rows; they are five distinct inputs, not 28 independent mistakes. All eight remaining failed Jev packets require RAN or power investigation, while the interpreter returns none for their fault report.

The draft annotations take the explicit `ran` or `power` prefix as the report’s domain. The frozen Jev criteria instead describe radio decoding/timing/equipment and electrical supply/voltage/power measurements. The generic operation text names none of those functions; its measurement metadata is intentionally withheld from the interpreter. A domain reading of none may therefore reflect that evidence boundary. The hosted model exposes no reasoning, so its cause remains unconfirmed. Before changing domain questions, inputs or references, the next study needs a definition of what the domain head should identify.

Metadata grouping resolves 14 Jev packets whose report meanings match both annotations. Under asset grouping, those correct meanings lead to incorrect NOC decisions; the candidate distinguishes their functions or declared conditions. It preserves all 18 Jev packets that already match both report and packet references. Eight additional packets still match triage despite wrong domain readings, under either policy. Correct packet agreement does not remove that interpretation disagreement.

Both ML models retain NOC on all 48 packets, leaving exactly half correct. Original ML returns unknown on every distinct report and mostly none for domain. Broader ML recognizes all stated domains but calls every fault report unknown; normal readings match. The policy cannot assign a fault domain that its reader never supplies. Broader vocabulary improves domain agreement without fixing fault recognition.

The rule reader recognizes `failure` in the condition-comparison fault texts but does not recognize `fails` or `malfunction` in the other fault wording. Its RAN domain expression matches radio/antenna/decoding, not the literal `ran` prefix. Metadata therefore fixes six rule-fed packets where both report meanings already match, while 18 matching packets still hide reading disagreements. These fixed expressions remain unchanged; their result is a control, not an updated candidate.

### Scope and eligibility controls

Both Jev paths retain NOC on the missing/ambiguous scope B packets. They also preserve both stale-normal B packets under either policy, assigning transport when the missing-scope report is stale. The unlinked missing-scope A packets remain NOC because their fault report receives domain none: Jev cannot test the desired RAN disposition there. Supplying the prewritten report meanings demonstrates that the policy itself excludes the unlinked scope report and assigns RAN. That is a reference diagnostic, not a model success.

The pack supplies its own function and condition identifiers. Incorrect but confidently declared metadata is not tested here. Neither a high score nor the conservative missing-scope checks establish that metadata is trustworthy.

## Next decision

The remaining Jev disagreements concern **instrument domain versus domain-specific technical evidence**. For example, `Independent ran observation: A current operation trace confirms a component failure during the measured operation.` carries a RAN prefix, but gives the interpreter neither a radio function description nor the supplied `radio_decoding` metadata.

I will keep this study frozen. The next domain comparison needs a choice: should the head identify an instrument’s declared domain, while policy separately checks service relevance, or require the report’s technical detail to establish that domain? Those definitions imply different annotations and inputs. Any change needs new families, prewritten references and a matched comparison; earlier references and scores must remain intact. Specialist review and final held-out evaluation remain pending.
