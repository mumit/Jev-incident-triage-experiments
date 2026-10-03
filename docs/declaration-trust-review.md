# When domain declarations disagree

## Boundary left by the completed study

The [declared-domain comparison](declared-domain.md) shows that software can supply domain while Jev reads the operation outcome on this synthetic pack. Every structured declaration agrees with its report header. The study tests neither conflicting declarations nor source authority.

The next metadata-trust comparison needs a reference rule for that disagreement. This is a policy choice, not a decision the previous scores can establish.

## A hypothetical input

Structured instrument metadata declares `ran`, while the report’s explicit `Instrument domain` header declares `power`. The report records a focal operation failure. Its measurement is current, its asset has a visible path to affected service, and its measurement scope is resolved.

This is a proposed test case, not a recorded failure. The operation can still be read as `fault`; the unresolved question is which declared domain can support an owner.

Two policies would produce different references:

| Policy | Initial owner | Next check | Evidence insufficient |
|---|---|---|---|
| Treat conflicting declarations as unresolved | NOC | Gather evidence to resolve the declaration | Yes |
| Treat structured instrument metadata as authoritative | RAN | Inspect radio | No |

I favor retaining NOC until the declaration conflict is resolved, because the lab has no verified instrumentation authority or lineage. If structured metadata is intended as the authoritative source, that assumption should be explicit and tested separately. Either choice preserves the operation reading and current affected-service link checks.

## Work after the choice

New development families can compare agreeing, missing, ambiguous, conflicting and stale declarations. The selected precedence rule must determine references before inference. Existing data, questions, references and results remain frozen. No conclusion here validates real instrumentation trust or authorizes automated network changes.
