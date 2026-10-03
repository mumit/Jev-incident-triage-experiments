# Analyst review plan

## Purpose

I will test analyst-facing recommendations before considering automatic routing. The [held-out synthetic evaluation](task-fit-analyst-evaluation.md) found a wrong core suggestion at probability 0.84. Its confidence boundary did not prevent every error, and the study has not measured analyst agreement or review effort.

This plan prepares a local review of real reports. It contains no real data, recorded specialist judgment or measured operational outcome. The user would need to identify the reviewers and supply appropriately handled reports before that work can begin.

## First review batch

A small batch of 20–40 historical reports can establish whether the task definitions and review form are useful. Include straightforward cases and ambiguous ones across RAN, transport, power and core. In particular, cover:

- Intake success with failed, delayed or unmeasured downstream completion.
- Historical alarms alongside current normal and current faulty measurements.
- Negation, absent traces, reset counters and allegations without confirming measurements.
- Multiple reports whose freshness, service linkage or declarations disagree.

Keep report meaning separate from incident ownership. The reviewer should identify what the report establishes about its measured function before assessing the service path and initial team. A handler can operate normally while the overall service remains degraded.

These deliberately selected cases help review definitions. They do not reproduce incident frequencies or establish a production error rate. Keep related reports from one incident together. A later evaluation needs a fresh time window and appropriate separation by incident, site or vendor group.

## Review before inference

| Record | What the reviewer supplies |
|---|---|
| Source | A local case identifier and original report, preserving contradictory and uncertain clauses. |
| Measured function | The function, its plain-language definition and what that measurement excludes. Mark missing scope explicitly. |
| Report reference | Fault, normal, unknown or unresolved; cite the evidence supporting the judgment. Unresolved cases have no scored answer yet. |
| Incident context | Currentness, observation time, declared domain, asset, comparison conditions and service linkage as available facts. Do not infer missing facts to make the case scoreable. |
| Initial-team reference | The analyst's recommended first team, the policy applied and the reason. It may differ from the synthetic teaching policy. |
| Disagreement | Preserve each review and its rationale. Reconcile disagreements before freezing a scored reference; do not overwrite the originals. |

Reviewers should assess the source before seeing Jev's answer. A second reviewer should independently check ambiguous scope or conflicting evidence. Agreement between reviewers is useful evidence about the task definition; it does not make an uncertain measurement certain. Proposed changes to policy or function definitions need a new version, leaving all historical references intact.

The initial collection stays local. This plan does not authorize sending real reports to a hosted provider. Any later inference needs an explicit data-use decision for that batch and destination.

## Compare the interpretation methods

After reference review, the next comparison can use new development families to test complete report text and function metadata against the same facts plus an explicit function definition. For intake, the definition could say: “Admission of valid requests to the handler; excludes downstream completion.” Neither input should insert a predicted reading or remove an inconvenient clause.

A fair ML comparison needs training examples that cover this task and the same available report/function facts as Jev. The old text-only bridge models do not meet that condition. Fit features and labels only on the training split, record unknown-class behavior and keep all methods under the same downstream policy. Another model provider remains outside the authorized work.

Development selects the reader and input. Fresh calibration data selects any display boundary; an untouched evaluation set checks the frozen system. The completed 24-case task-fit evaluation can illustrate failures but cannot select the revised reader or threshold.

## Measure analyst assistance

The analyst retains the assignment and records whether the suggestion was accepted, corrected or unusable, with the reason. Separate a wrong report interpretation from wrong metadata, policy disagreement and missing evidence.

Measure review time and clarification effort alongside report errors, wrong domain suggestions, unknown readings, qualifying coverage and failed calls. Compare assisted and unassisted reviews on matched case difficulty. Avoid having the same analyst reread a memorized case in both conditions; record the review order and method. Small batches can test the workflow, but need not support reliable time-saving estimates.

No operating error limit, useful coverage target or workload benefit has been established. Those decisions should follow specialist review and measured analyst evidence rather than inherit the synthetic research gates.

## Current dependency

The protocol and inspection tool are ready for review. A range of real reports, identified reviewers and agreed reference meanings are not available in this repository. Those inputs are necessary to answer whether Jev helps this network team's actual triage work. Further synthetic cases can study input design, but cannot replace that evidence.
