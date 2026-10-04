# Moving to public operations data

## Decision

I will use RCAEval for the first public-data comparison. OpenRCA's Telecom subset is closer to the domain, but its telemetry carries a noncommercial restriction. RCAEval supports individual-case downloads and publishes permissive data terms. This choice keeps the learning experiment portable without assuming permission for company use of OpenRCA.

The completed synthetic studies remain frozen. Public telemetry introduces a different task and different references, so its scores will not be accuracy deltas from those studies.

## OpenRCA inspection

The [OpenRCA paper](https://netman.aiops.org/wp-content/uploads/2025/05/13411_OpenRCA_Can_Large_Langua.pdf) describes a telecom database system with operating systems, pods, databases and Redis. It supplies metrics and traces, but no logs. This is relevant to service operations; it does not represent radio-access KPIs or field-service work. The paper specifies CC BY-NC 4.0 for telemetry. The repository's MIT licence covers its code.

The public archive is accessible. HTTP range requests allowed selective extraction without downloading the full archive. CRC checks verified the query file, reference file and one middleware metric file. The inspection found:

| Item | Observed contents |
|---|---|
| Archive | 3,071,992,930 compressed bytes; 17,658,622,120 expanded bytes, including metadata files. |
| References | 51 failures across 11 dates; CPU, connection-limit, database-close, network-delay and network-loss labels. |
| Queries | 51 tasks. `instruction` contains the request; `scoring_points` contains answer text. |
| Metric sample | 95,038 rows across 264 series and 12 middleware components on May 23, 2020. |

Only query instructions can enter model inputs; neither scoring points nor reference records may enter them. The inspected metric timestamps use milliseconds, while reference timestamps use seconds. Local dates need an explicit UTC+8 conversion. These checks apply to the inspected files; a complete importer must validate each additional schema.

The inspection establishes access and structure, not Jev performance. OpenRCA remains an alternative if its data terms suit the intended use. [Download and task definitions](https://github.com/microsoft/OpenRCA).

## RCAEval inspection

[RCAEval](https://github.com/phamquiluan/RCAEval) supplies controlled failures in microservice applications with root-cause service labels. Its published index contains 735 cases. The RE2 Online Boutique subset has 90 cases with metrics, logs and traces; all 90 index entries report samples before and after fault injection.

The [Hugging Face data card](https://huggingface.co/datasets/phamquiluan/RCAEval) declares MIT. The [original Zenodo distribution](https://zenodo.org/records/14590730) declares CC BY 4.0. The notices differ; preserve attribution to the authors, paper and original distribution when sharing results or derivatives. Record the downloaded distribution and revision rather than applying the code licence to every data copy.

Three exploratory cases cover a checkout-service CPU fault, a currency-service delay and an email-service socket fault. The local download preserves the published files and verifies their hashes. These cases and their service/fault repetition groups belong to development inspection. They cannot become a later held-out test.

Source directory names reveal the faulty service and injected fault. The case index also contains answers. A model request must receive a separately constructed packet, never a source path, index row or file listing. Actual telemetry service names remain useful observations and stay visible.

## Preparing the input

The preparation tool separates three layers:

1. **Source evidence:** unchanged metrics, logs and traces, with download hashes.
2. **Input-only calculations:** metric coverage, missing values, before/after distributions and changes, linked to source columns. Source paths and answer metadata stay outside model packets.
3. **Evaluation references:** the published faulty service and fault type, stored separately from prepared inputs.

The first draft uses metric summaries. Logs and traces are downloaded and profiled but do not yet enter Jev inputs. Trace service names differ from metric names in some rows, and trace timestamps use additional scales. Their mapping and units need checks before combining them. Missing values remain missing; the tool does not fill them with successful measurements.

Preparation uses the known injection time to define before/after windows. That is a controlled benchmark condition, not a detector discovering the incident. Later comparisons must state whether they receive a known incident window or detect it themselves.

The three downloads total 31,687,706 bytes, excluding the 29,500-byte case index. Each metric table has 1,441 timestamps: 720 before injection and 721 at or after it. The packets retain all 12 observed service candidates and the 12 largest metric median changes. Ranking divides the absolute median change by the larger of the baseline p90-p10 range, 1% of its absolute median, or a numerical floor of 1e-12. The packet states this rule; the resulting score measures a change, not its cause or probability.

On a fresh checkout, prepare and verify the local sample with:

```bash
uv run --locked --extra public-data python -m scripts.prepare_public_data download --folder runs/public-data/preflight-2026-10-03-v1
uv run --locked --extra public-data python -m scripts.prepare_public_data prepare --folder runs/public-data/preflight-2026-10-03-v1
uv run --locked --extra public-data python -m scripts.prepare_public_data verify --folder runs/public-data/preflight-2026-10-03-v1
```

The commands refuse to overwrite recorded downloads or prepared outputs. Use another folder for a new preparation version. The optional dependency reads Parquet; it downloads no model weights.

## Inspecting a transformation

These are observations from the prepared packets, not model predictions. Metric values retain their source units; the comparison uses relative changes.

| Prepared case | Source column | Before median | After median |
|---|---|---:|---:|
| `PUB-97bf1c72d29f` | `checkoutservice_cpu` | 0.41785 | 19.99256 |
| `PUB-d20ce8215231` | `currencyservice_latency-50` | 0.004096 | 0.100340 |
| `PUB-2cf334d2e0a4` | `emailservice_socket` | 3 | 9 |

For the delay case, the prepared state carries this evidence fragment:

```json
{
  "service": "currencyservice",
  "metric": "latency-50",
  "source_column": "currencyservice_latency-50",
  "before_valid": 720,
  "after_valid": 721,
  "before_median": 0.004096026122220065,
  "after_median": 0.10033980582524268,
  "change_score": 214.0532773356848
}
```

The same packet includes latency changes in checkout and frontend services. That allows a later reader to compare a local change with symptoms elsewhere rather than see only the known faulty service. The published answer, fault name and original directory are absent from the state. The complete packet is in `prepared-inputs.json`; `references.json` holds the answer separately.

These examples contain clear direct changes. They test the pipeline and input visibility, but cannot establish that Jev adds value over a simple change ranking. A broader comparison needs cases with propagation, competing symptoms and missing evidence.

## First public-data comparison

The question is: **Does Jev improve identification of the faulty service over a statistical or ML baseline on the same evidence?** Root-cause service is a published target. Investigation owner, urgency and recommended action are not supplied reference labels here.

Development will compare the baseline ranking with Jev's selection from the same candidate services and evidence, including an insufficient-evidence option. Anomaly detection and root-cause selection will receive separate scores. A well-detected symptom does not necessarily identify the component that caused it.

Before inference, freeze the source revision, grouped splits, window definition, transformations, candidate construction, baseline settings, Jev questions and evaluation rules. Keep repetitions of a service/fault combination within one split. Select input changes on development, any display boundary on calibration, and assess the frozen system on untouched groups. Evaluate candidate retrieval as well as final selection so an omitted true cause counts as a pipeline failure.

Results will include incorrect confident selections, withheld recommendations, missing/failed calls, latency and provider usage alongside accuracy. Every recommendation remains analyst-facing. A public benchmark can establish capability within its systems and fault coverage; operational usefulness for a particular network still needs later evidence.

## Recorded status

The dataset assessment and input preparation are complete. This stage makes no Jev calls and records no new ML or Jev performance scores. `checkpoints/public-data-assessment-2026-10-03.json` records source revisions, file hashes, observed schemas and local case profiles. Raw telemetry, prepared packets and reference files stay in ignored `runs/public-data/`.

Use the [handoff](../HANDOFF.md) for the current next task. The existing synthetic evaluation remains available in the [task-fit study](task-fit-experiment.md).
