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

## Results and follow-up

Inference has not run. The review will compare each reader under both policies, showing packet fixes/losses, newly wrong fields, unique-text understanding and wrong readings hidden by matching triage. Missing-scope cases must remain conservative, while stale and unlinked reports must remain excluded from grouping. This pack tests an explicit supplied schema. It cannot establish that a real network can provide equivalent metadata reliably.
