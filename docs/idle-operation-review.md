# Reading a handler that has not been exercised

## Deferred decision

On October 2, the user deferred this choice to examine [Jev's fit for incident triage](jev-task-fit.md). The definitions below remain unresolved. Do not construct scored idle cases or their training targets until the choice is made.

## Why the training comparison needs this decision

The [declaration guard study](declaration-trust.md) leaves both ML controls at 0/40 correct operation readings. Each reports `unknown`, even for explicit faults and successful operations. The deferred training comparison would cover instrument-report formats across fault, normal and unknown classes, on separate training and development families. Adding only easy fault and normal sentences could improve their scores while weakening appropriate uncertainty.

A useful uncertainty control needs a reference decision before it enters training or evaluation. The earlier [normal-handler choice](report-language-review.md) establishes that successful acceptance is normal for the measured handler. It does not decide how to read a handler that has accepted no requests because none arrived.

## Input to resolve

A current instrument declares `core` and measures `request_intake` under a resolved comparison context. The raw report says:

> The handler processed zero requests during this interval. Its error counter remained at zero. No request exercised the handler.

Assume a visible path to the affected service. The report makes no claim about successful acceptance, an active availability test or a measured fault. This is a hypothetical input, not a scored example or a recorded model failure.

| Reading definition | Reference for this report | What it assumes |
|---|---|---|
| Require evidence of an exercised operation | Unknown | A zero error count without operations does not demonstrate the handler’s performance. |
| Treat a clean monitored interval as normal | Normal | Absence of reported errors establishes normality even without observed requests. |

Either reading leaves NOC ownership under the current degraded-service policy because neither establishes a fault. Packet matches could therefore conceal the difference. The report annotation and its classifier training target would differ.

## Work after the choice

The selected definition will determine new idle-operation annotations before fitting. A matched comparison will retain the same training counts, labels, model settings and software policy across arms, changing report format coverage alone. Further development families will include exercised successes, explicit faults, unconfirmed outcomes and idle intervals. Existing training, references, questions and measured results remain frozen. These teaching definitions still need specialist review before operational validation.
