# What should the domain head identify?

## The decision

The metadata study leaves a task-definition ambiguity. Its draft annotations accept the report’s stated domain; the frozen Jev question describes domain-specific technical functions. Those definitions differ when a generic operation report names its source but omits the function.

For the next study, the choice is between:

- **Declared instrument domain:** identify the domain named by the instrument or report. Policy separately checks currentness and its connection to the affected service. A domain name alone does not assign investigation ownership.
- **Technical evidence domain:** identify a domain only when the report’s technical detail establishes it. A source prefix alone can receive `none`.

I favor the first definition because it keeps source identification separate from service relevance. That choice still needs confirmation, followed by new families and prewritten references. The current data, questions and results remain frozen.

## A recorded example

Packet `NMP-99de43f119cf-a` includes a report with this normalized text:

> Independent ran observation: A current operation trace confirms a component failure during the measured operation.

Both Jev controls return `domain: none` and `reading: fault`. The original domain question assigns `ran` to radio processing, decoding, timing or radio-equipment measurements. The text identifies a RAN source but describes none of those technical functions.

Policy separately receives declared `radio_decoding` scope and `condition-A`. Jev receives neither field. The draft report reference is `ran / fault`; it takes the source prefix as authoritative. The disagreement therefore cannot establish that Jev failed under a settled domain definition. Its hosted responses expose choices and probabilities, not reasoning.

The [metadata workbench](http://127.0.0.1:8768/metadata-policy?case=NMP-99de43f119cf-a&arm=jev_focal__metadata&report=0#input) shows the exact request, separate policy facts and saved response. Reveal draft references to compare both policies with the report annotations supplied as an evaluation diagnostic.

## What follows the choice

A separate matched comparison will keep operation-outcome interpretation and metadata policy fixed, use further development families, and version the domain definition explicitly. Its controls must include missing or ambiguous domain declarations and reports outside the affected-service path. Neither option justifies relabeling the existing pack or treating these synthetic results as operational validation.
