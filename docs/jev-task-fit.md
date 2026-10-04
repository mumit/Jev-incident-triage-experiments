# Is Jev a good fit for incident triage?

Research checked October 2, 2026. Local evidence checkpoint: `3a9f54c`.

October 3 direction update: the user selected public data to examine broader operations capability without access to real reports or specialist-reviewed triage references. The [public-data assessment](public-data-assessment.md) records source inspection and selects RCAEval for the next comparison. The October 2 research and completed synthetic results below remain historical evidence.

## Assessment

Jev is a credible candidate for bounded interpretation within telecom incident triage. The evidence does not yet establish that it is the best model for the complete task, or that its decisions support unattended operation. I will continue evaluating it as a report interpreter, with software handling evidence eligibility, scope, declaration consistency and policy.

Public examples show working integrations and encouraging development results. I did not find a publicly documented production telecom deployment with independently validated outcomes in the sources reviewed. That is a limit of this review, not proof that such deployments do not exist.

The idle-handler reading choice is deferred. Existing inputs, questions, references, predictions and checkpoints remain frozen; this review adds no inference results.

## How others use Jev

The following sources describe their authors' implementations. Their scores use different tasks and populations and cannot form a model ranking.

| Implementation | Jev's role and reported evidence | What the evidence supports |
|---|---|---|
| [unoblox NOC/SOC replay](https://unoblox.ai/blog/jev-noc-soc-automation) | Rules handle clear cases; Jev interprets unresolved narratives and proposes incident association, another observation or analyst review. Revised rules plus Jev match 35/40 synthetic labels versus 32/40 for rules. Of 20 attempted requests, 18 succeed. | A development example across ten templates, revised after the first pass. Critical cases bypass Jev. No demonstrated reduction in restoration time or production workload. |
| [reachjalil log-paging study](https://huggingface.co/datasets/reachjalil/jev-luna-pagerduty-trigger) | On 3,000 synthetic payment logs, categorical urgency misses all 57 INFO-level replica-lag incidents. Looser wording produces 189 false pages. A focused binary question with an application threshold reports 500/500 incidents caught and zero false pages. | Question design and decision thresholds matter. The same development stream guided revisions; the result does not establish telecom performance. The comparator's unavailable responses are excluded from its rates, so failure denominators differ. |
| [RuleRaven](https://github.com/ddalcero/ruleraven) | A Kubernetes controller normalizes observations, applies rules, calls Jev for ambiguous cases and composes decisions in code. An Alpha EKS smoke deployment exercises a live decision and notification delivery. | A practical integration pattern. The author explicitly distinguishes the smoke test from production readiness. No comparative accuracy benchmark or operational history is reported. |
| [kenhuangus SOC harness](https://github.com/kenhuangus/jev-usecases) | Closed Jev questions feed coded triage, investigation, mitigation and escalation procedures. The runners return action names; they do not execute containment. Live fixtures check the typed interface. | Reusable workflow code. Successful fixture responses do not measure correctness; the author says thresholds and procedures need validation before unattended use. |
| [triagedy SOC classifier](https://github.com/m0rphtail/triagedy/blob/main/docs/ACCURACY_BENCHMARKS.md) | Typed judgments feed disposition policy. The published telemetry result is 64/64 correct on 64 process events selected from an Atomic Red Team capture. | That sample contains one simulated attack and 63 routine processes. Its perfect score does not establish broad attack recall, production noise reduction or calibrated confidence. |
| [Atlan Digital secret-exposure triage](https://www.atlan.digital/lab/sharpmlv2-jev-ai-soc.html) | A detector sends masked candidate records to Jev. On 300 surviving synthetic cases, Jev's Brier probability-error score is 0.0337 versus 0.0959 for a simple heuristic; lower is better. | Useful task-specific probability evidence, with a disclosed corpus-generation error that changed class prevalence. The study does not validate calibration at the intended operational base rates. |
| [Jev-IDS preprint](https://arxiv.org/pdf/2610.01079) | One serialized network flow receives an attack-probability question and a traffic-category question, optionally with labeled examples. | Experimental intrusion classification, not incident investigation. The abstract describes 300 flows and one comparator; the body describes 2,000 flows and another. I exclude its quantitative superiority claims from this assessment until those inconsistencies are resolved. |
| [Trau coding workflow](https://trau.sh/blog/typesafe-jev-case-study) | Jev supplies ticket complexity, readiness, relevance and duplicate judgments; code owns model routing and consequences. Model and question versions are pinned. | An adjacent product author's account of use, not SOC/NOC evidence. It reports no accuracy benchmark on its own data. |

The closest examples place Jev between observations and coded decisions. They do not establish that Jev can independently investigate an unfamiliar outage, determine its cause or execute a reliable remediation plan. This is my interpretation of the implementations above.

## What the Northstar Telecom lab establishes

| Recorded comparison | Result | Interpretation |
|---|---|---|
| [Direct triage versus report interpretation and fixed policy](report-language.md) | 127/140 → 139/140 complete-packet matches. Five report readings remain wrong, four concealed by matching triage. | Separating interpretation from policy helps on this constructed pack. Several components change, so the gain cannot be attributed to a prompt alone. |
| [Measured-function reading question](report-scope.md) | 82/88 → 83/88 correct report readings; 67/68 → 68/68 packet matches. Two readings improve and one regresses. | Defining the measured function helps a boundary case, but an aggregate gain conceals a regression and policy gaps. |
| [Declaration consistency guard](declaration-trust.md) | 56/80 → 80/80 packet matches with the same 40/40 correct Jev operation readings. | The gain comes entirely from software policy. Jev does not become a better reader in this comparison. |

These are separate development packs, not points on one accuracy trend. Correlated variations, deliberately written language and provisional references limit every result. Repetition has also exposed answer changes on identical requests. Neither packet agreement nor stable output establishes operational correctness.

The frozen ML controls struggle with later report formats. That identifies a training-coverage gap; it does not establish Jev's superiority over a well-trained incident classifier. The lab also lacks a matched, capable structured-output language-model comparator.

## Where Jev belongs

| Work | Intended component |
|---|---|
| Interpret whether a report establishes a fault, successful operation or an unconfirmed outcome for a named function | Jev candidate, evaluated against independently reviewed report labels. |
| Judge whether narrative evidence fits a shortlisted known incident, or whether a particular read-only observation is missing | Further bounded Jev tasks, each requiring its own evaluation. |
| Compare timestamps, calculate impact priority, traverse supplied dependencies and check explicit declaration consistency | Software with visible inputs and traces. |
| Detect anomalies in raw KPI time series | A separately evaluated statistical or ML detector; Jev can subsequently interpret the resulting evidence. |
| Reconstruct an unfamiliar outage across many systems, generate an investigation plan or explain a cause | Analyst or a separately evaluated reasoning system. |

TypeSafe recommends atomic questions composed in code. Questions in one request are evaluated independently against the same state; an ownership question cannot consume another question's predicted report reading within that call. Dependent decisions need software composition or a subsequent request with the new evidence. [Official introduction](https://docs.typesafe.ai/introduction).

The vendor documents literal interpretation, weak arithmetic and date comparison, sensitivity to irrelevant context, option-order effects and adversarial text. These directly motivate filtered evidence, precise criteria, software calculations and explicit robustness checks. Typed output still permits a wrong classification. [Known limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13).

## How to improve performance

### Make the task explicit

The next target is report meaning for a named measured function. Initial investigating owner remains a downstream policy decision, distinct from root cause. Keep `unknown` for reports that do not establish the outcome. A normal reading for request acceptance does not establish successful session completion.

### Change the input without concealing the change

This is an illustrative candidate input, not a recorded request:

```json
{
  "focal_function": "registration_acceptance",
  "report_text": "The registration handler accepted the request. Downstream session completion remains unconfirmed.",
  "source_reference": "report-17"
}
```

Ask: **“What does this report establish about the registration-acceptance handler?”** Define `normal` as explicit successful acceptance, `fault` as explicit failure or refusal of that operation, and `unknown` as insufficient evidence of its outcome. Keep downstream completion as a separate observation. This applies the selected normal-handler teaching definition; it does not resolve idle intervals.

Software should obtain the focal function from supplied instrument metadata, rather than derive it from an answer key. Preserve the original report and its source reference. Currentness, service linkage and declaration consistency remain separately calculated policy inputs. Do not insert a calculated `fault` flag, discard a contradictory clause or rewrite the report into its expected answer.

Compare formats carrying identical facts before adding context. If an arm introduces a focal function that its control lacks, label that comparison as added information rather than formatting alone. Clause selection, abbreviations and removal of identifiers each need a separate check for lost meaning.

### Test examples and thresholds

A small set of reviewed examples could clarify negation, successful acceptance, downstream uncertainty and historical alarms. Treat this as an untested candidate: examples must come from training families, and adding more examples must earn its place through validation.

Record the full returned distribution. Choice confidence is a normalized measure of concentration above a uniform distribution, not an observed probability that the answer is correct. For three options, a top probability of 0.90 produces confidence 0.85. Noul returns the probability of its yes proposition. Thresholds must therefore be evaluated for the specific question type, model version and task. [Official confidence definition](https://docs.typesafe.ai/confidence).

### Preserve a traceable pipeline

Source reports → software evidence checks → focused Jev readings → fixed policy → recommendation or review.

Every recommendation should expose the source, exact request, actual response and policy trace. Failed calls retain an explicit review outcome. Cache only when all meaning-bearing inputs, question definitions and model version match; removing timestamps, assets or numeric values can merge cases with different meanings.

Current Jev customization happens through state, instructions, criteria and decomposition. TypeSafe says it does not fine-tune or apply customer-specific LoRA weights. Pin `jev-1.13.0` during comparisons rather than a moving alias. [Official model reference](https://docs.typesafe.ai/models).

## Next experiment

October 3 update: the [task-fit experiment](task-fit-experiment.md) now records development, repeatability, frozen-reader calibration and a [held-out analyst-facing evaluation](task-fit-analyst-evaluation.md). Its `/task-fit` workbench exposes measured requests and responses. The plan below records the October 2 research direction; the user selected analyst-facing recommendations. The frozen 0.60 advisory boundary lets through one wrong core suggestion, failing the provisional zero-error criteria. No automatic-routing threshold or operational error budget is approved.

I will prepare a task-fit study before another targeted ML training change. Its protocol will answer whether Jev interprets a broader range of reports correctly, how much review it needs and which input changes improve those outcomes.

1. **Write new cases and review their references.** Cover RAN, transport, power and core reports, including counter resets, negation, historical alarms, successful intermediate operations, unresolved downstream outcomes, multiple faults and misleading instructions. Keep idle cases outside scored comparisons until the deferred definition is resolved. Synthetic results remain teaching evidence; representative operational claims require appropriately handled real examples and specialist review.
2. **Separate development, calibration and final evaluation families.** Development selects the input and question; calibration selects thresholds after those freeze; a sealed evaluation set measures the resulting system. Related templates stay within one split. Later operational evaluation should also separate incidents by time and relevant site or vendor group.
3. **Change one component at a time.** Compare equivalent-fact prose and structured inputs with questions fixed, then test focused wording with inputs fixed, then train-only examples. Keep policy fixed throughout. Preserve the current implementation as a bridge control, clearly identifying any difference in available facts.
4. **Measure interpretation and triage separately.** Report fault, normal and unknown errors; complete-packet and paired results; wrong readings hidden by matching decisions; high-impact misroutes; failed calls; latency and cost per incident. Count distinct reports and families separately from occurrences and repetitions.
5. **Evaluate the review boundary.** Show how error changes as more decisions proceed without analyst review. Select thresholds on calibration families, include uncertain and failed responses in workload totals, then check the frozen choices on sealed families. The minimum useful coverage and acceptable error limits remain operational decisions, not assumptions borrowed from a demo.
6. **Establish comparative fit.** Rules and the current ML model remain controls. A later matched comparison needs an adequately trained ML classifier and a capable structured-output language model on the same evidence and policy. Adding another provider remains a separate execution decision; this review neither installs nor calls one.

Jev earns further use if it improves useful decision coverage at an acceptable error level and meets incident-level latency and cost limits on new evaluation cases. If failures require missing measurements, better instrumentation is the remedy. If literal wording remains unreliable despite clear inputs, those decisions should stay with a different interpreter or an analyst. Once the evidence supports routing recommendations, shadow operation can measure analyst agreement and workload before any automated action expands.
