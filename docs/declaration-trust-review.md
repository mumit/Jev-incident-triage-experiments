# When domain declarations disagree

## Boundary left by the completed study

The [declared-domain comparison](declared-domain.md) shows that software can supply domain while Jev reads the operation outcome on this synthetic pack. Every structured declaration agrees with its report header. The study tests neither conflicting declarations nor source authority.

On October 2, 2026, the user selected **retain NOC until the declaration conflict is resolved**. The report’s operation reading remains separate. This is a synthetic teaching rule, not verified instrumentation authority.

## A hypothetical input

Structured instrument metadata declares `ran`, while the report’s explicit `Instrument domain` header declares `power`. The report records a focal operation failure. Its measurement is current, its asset has a visible path to affected service, and its measurement scope is resolved.

This is a proposed test case, not a recorded failure. The operation can still be read as `fault`; the unresolved question is which declared domain can support an owner.

Two policies would produce different references:

| Policy | Initial owner | Next check | Evidence insufficient |
|---|---|---|---|
| Treat conflicting declarations as unresolved | NOC | Gather evidence to resolve the declaration | Yes |
| Treat structured instrument metadata as authoritative | RAN | Inspect radio | No |

The selected rule retains NOC until the declaration conflict is resolved. If structured metadata is intended as the authoritative source, that assumption should be explicit and tested separately. Either choice preserves the operation reading and current affected-service link checks.

## Work after the choice

New development families can compare agreeing, missing, ambiguous, conflicting and stale declarations. The selected NOC rule will determine new references before inference. Existing data, questions, references and results remain frozen. No conclusion here validates real instrumentation trust or authorizes automated network changes.
