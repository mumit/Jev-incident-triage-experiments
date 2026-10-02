# Experiment 3: report interpretation and policy

October 2, 2026. This study separates two jobs: interpreting an observation and applying the incident policy. A report can describe a power fault even when stale evidence or an unknown service path means NOC should investigate first. Earlier packet classifiers learned those decisions together; this comparison exposes the intermediate reading.

Report ML followed by fixed policy gets 62/108 new development packets right, compared with 55/108 for matched packet ML and 70/108 for the previous frozen candidate. Its reading errors outweigh the benefit of separating the jobs. I will retain the previous candidate and test broader report wording next. Jev makes no calls in this study.

## Data and annotations

The new learning set contains 186 packets in 31 families and 210 reports. Development contains 108 packets in 27 further families and 124 reports. A family shares a scenario mechanism and template; each pair changes one field, such as a dependency edge, measurement time or report detail. Training and development families do not overlap with each other or earlier studies, but they share simplified vocabulary and mechanisms. The packets and pairs are correlated teaching examples, not representative network data or final held-out evaluation.

Each report has a separately written domain annotation (transport, RAN, power, core or none) and reading annotation (fault, normal or unknown). “Written” means I specified the intended meaning with the report template before fitting. These annotations do not come from the packet's triage answer. For example:

```text
Report: Independent power tests at [asset] report that equipment voltage is absent;
        independent service probes confirm interruption.
Report annotation: power / fault
Packet evidence: measurement is stale
Packet reference: NOC / gather evidence / insufficient evidence
```

The report describes a power fault. Its meaning stays separate from whether policy can use it. A packet with current evidence and a visible affected-service path can justify power investigation; the same report with a stale measurement cannot.

Development pairs cover visible service paths, stale and unknown measurements, current contradictions, negation, uncertainty and missing inventory. Recovery, unexplained maintenance and unclassified reports provide controls. Every domain appears literally in the report prefix, making domain classification easy. The 15-minute inclusive validity window, same-asset conflict grouping and diagnostic references remain provisional; specialist review is pending.

## Inputs and inference paths

| Path | Training or interpretation | Final decision |
|---|---|---|
| ML · frozen candidate | Previous combined-feature recipe and unchanged 96-packet training set | Four fitted packet heads |
| ML · matched packet | Same recipe and settings, fitted on the new 186 packets and packet references | Four fitted packet heads |
| Report ML → policy | Text-only domain and reading heads, fitted on 210 separate report annotations | Fixed policy |
| Report rules → policy | Explicit domain, uncertainty, normal and fault expressions; no fit | The same fixed policy |
| Rules | Unchanged original incident rules | Original rule decisions |

Matched packet ML and Report ML receive the same raw training and development packets. Their supervision, feature units, model heads and policy implementation differ. The report pipeline adds observation annotations and explicit asset grouping. This is an architecture and supervision comparison, not a capacity-controlled test or a feature-only intervention. The previous 96-packet candidate serves as a separate bridge control.

For Report ML, normalized report text enters word TF-IDF (ngrams 1–2) and character TF-IDF (ngrams 3–5). Two logistic heads predict domain and reading. The vocabulary fits training reports only; minimum document frequency is 2, term frequency is sublinear, classes are balanced, C=2, maximum iterations 2,000 and random state 17. Asset identifiers become a generic asset token. Topology, timestamps, impact, changes and answer keys never enter this text classifier.

Policy then joins each predicted meaning to its observation index, asset, freshness and visible affected-service path. A current supported unique fault selects that domain; current comparable fault/normal readings at the same asset retain NOC. Stale or unlinked faults do not justify domain ownership. Priority follows impact and affected sites. Recovery and maintenance have explicit branches. These are decision rules, distinct from the earlier input-only calculators that derive paths and ages without classifying faults.

Report rules use uncertainty and negation before fault expressions. They also classify meaning, rather than merely calculate input facts. I wrote these expressions alongside the pack and fixed them before measurement. They cover its development vocabulary, while ML learns only the training phrases; this gives rules a coverage advantage and makes their comparison a diagnostic rather than a blind transfer test. Both interpreters retain every report, including evidence policy cannot use. Report ML probabilities describe its domain and reading choices; final policy decisions have no fitted probabilities.

## Results

Run `development-2026-10-02-v1` saved its protocol, source hashes and data hashes before fitting. The [recorded report](../checkpoints/experiment-3-interpretation-2026-10-02.json) contains predictions' scores, attribution and field regressions. Sources and data are frozen after this run.

| Path | All four correct | Both packets correct | Owner / next check / evidence correct |
|---|---|---|---|
| ML · frozen candidate | 70/108 (64.8%) | 20/54 (37.0%) | 72.2% / 73.1% / 84.3% |
| ML · matched packet | 55/108 (50.9%) | 9/54 (16.7%) | 56.5% / 51.9% / 55.6% |
| Report ML → policy | 62/108 (57.4%) | 16/54 (29.6%) | 57.4% / 57.4% / 57.4% |
| Report rules → policy | 108/108 (100%) | 54/54 (100%) | 100% / 100% / 100% |
| Rules | 56/108 (51.9%) | 4/54 (7.4%) | 55.6% / 51.9% / 55.6% |

Priority matches every draft reference in every path. Against matched packet ML, Report ML fixes 15 complete packets and loses eight, introducing 12 wrong owner fields, eight wrong checks and 12 wrong evidence fields. Against the previous frozen candidate, it fixes 13 and loses 21. Aggregate gain over the matched arm therefore does not support replacing the previous candidate.

Report ML gets all 124 domains right but only 50/124 readings right (40.3%). Sixty transport, RAN and power fault reports become normal; six normal power reports become faults; eight uncertain reports become faults. Its 62 correct packets include 24 with at least one wrong report reading. Correct triage can mask an interpretation error when the report is ineligible or NOC remains the final choice for another reason.

Report rules get every domain and reading right on this pack. Their 100% packet score reflects deliberately simple authored expressions and a policy aligned with the draft references. It does not establish robust language understanding or operational accuracy. Multiple clauses, uncertainty about an unrelated check and unseen terminology would challenge these expressions.

An evaluation-only diagnostic feeds the written development annotations into policy after actual predictions. It matches all 108 draft packet references. This checks consistency of the policy implementation with those references; it is not model performance, an attainable accuracy estimate or independent validation of the policy. No packet with entirely correct Report ML readings fails the draft policy decision here.

## Where the report model fails

### Service probes become a shortcut for normal

In `NSI-1767d4f9988a-a`, a current supported transport report says:

```text
packet loss is present; independent service probes confirm interruption
```

Report ML selects normal at 50.1%, versus fault at 37.7%. Policy consequently retains NOC and asks for more evidence. The fitted normal-over-fault log-odds margin is +0.283. Each of the word features `independent service`, `probes`, `service` and `service probes` contributes +0.155 toward normal. In training, that language appears only in normal recovery reports. The new fault report therefore activates a learned wording association that contradicts its meaning. Other features and the intercept also contribute; deleting one word is not a demonstrated fix.

### Uncertainty becomes a fault

In `NSI-0566b2bf8a52-b`, packet loss is “suspected” and the measurement “inconclusive.” The model selects fault at 68.4%, and policy assigns transport. Training uncertainty uses “might be failing” and “unconfirmed” instead. Character features can partly overlap, but this result exposes poor transfer between uncertainty expressions.

### A correct answer hides a missed conflict

In `NSI-c3ac8df8f332-a`, current transport reports contain a fault and a normal reading. Report ML calls both normal. Policy still returns the correct NOC/gather-evidence/insufficient-evidence decisions, but its trace shows no recognized conflict. In packet B, only the nominal reading becomes stale. The missed fault now produces the wrong NOC decision. Inspecting the intermediate reading explains why the correct A answer is insufficient evidence of understanding.

## Next experiment

I will broaden the report training wording while keeping the report classifier, input boundary and policy fixed. A matched comparison should replace redundant training phrases at the same packet count and domain/reading mix, distribute service-probe language across fault, normal and unknown reports, and vary positive, negated and uncertain descriptions without changing their meanings.

Further development families should test those distinctions and contain clause-scoped negation and uncertainty controls. The existing 108 packets are now inspected development evidence; they cannot validate the next revision independently. Report-level accuracy, complete-packet fixes, field regressions and errors hidden by correct triage must remain visible. The original packet candidate stays unchanged. Specialist review still precedes final held-out evaluation.

## Inspect and reproduce

[Open the report-policy workbench](http://127.0.0.1:8768/experiment-3?trial=interpretation&case=NSI-1767d4f9988a-a&variant=reading#decisions). **Exact input** separates interpreter text from policy facts. **Decisions** shows each predicted meaning, the fixed policy trace and the saved report vector and score contributions. Reveal draft references separately; they never enter an exported inference input. Training packets show annotations and inputs without evaluation predictions.

```bash
uv run --locked python -m scripts.run_experiment3_interpretation validate
uv run --locked python -m scripts.run_experiment3_interpretation run --output runs/experiment-3-interpretation/my-report-study
uv run --locked python -m scripts.run_experiment3_interpretation verify --output runs/experiment-3-interpretation/my-report-study
```

Runs are immutable. Raw evidence stays under ignored `runs/experiment-3-interpretation/`. A fresh clone can inspect inputs and annotations and replay the local study without Jev. The historical public bundle remains unchanged and does not include this run. Nothing in the lab executes network changes.
