# Report-language reference decision

## What needs a decision

The next report-reader experiment needs a precise definition of a normal core measurement. The current draft treats this observation as **core / normal**:

> The registration handler accepts subscriber requests across independent access routes.

Its paired refusal observation is **core / fault**. These annotations describe the focal handler, not proof that the entire service has recovered. They were written before inference.

Jev calls five acceptance rows unknown in the 156-report development run. Those rows contain two distinct normalized texts. A diagnostic replay repeats both texts and matched refusal controls three times. One acceptance text gives unknown, normal, unknown; the other gives unknown every time. Refusal remains fault in every repeat. The hosted model does not expose its reasoning, so the result alone cannot establish why it selects unknown.

The current acceptance-versus-refusal conflict case makes the consequence visible: **[inspect the current conflict](http://127.0.0.1:8768/report-language?split=development&case=NSL-c9841c3176a5-a&arm=jev_reading#inspect)**. When Jev calls acceptance unknown, fixed policy no longer recognizes a current normal/fault contradiction and assigns core. Direct Jev retains NOC. The existing reference and recorded regression remain unchanged.

## Two possible definitions

| Definition for the next study | Acceptance without completion | Explicit refusal | What changes |
|---|---|---|---|
| Focal handler measurement | Normal: the stated handler behavior succeeds, while wider service status remains separate | Fault | Keep the current meaning boundary. Clarify that normal applies to the focal measurement rather than proving complete service recovery. |
| Completed registration measurement | Unknown: acceptance alone does not establish completion | Fault, provided refusal represents a fault rather than expected rejection | Require completion evidence before a normal reading. Specify how successful, partial and rejected registrations relate to the measured function. |

I favor retaining the focal-measurement definition for the synthetic continuation because it preserves the separation between report meaning and service impact. A network specialist may identify a better measurement boundary. In either case, choosing a definition does not validate the 15-minute threshold, same-asset comparability or topology assumptions.

## What follows the decision

The next pack should distinguish accepted requests, completed registrations, partial success, expected rejection, malfunction-driven refusal and uncertainty about completion. Current versus stale comparisons must preserve their report meanings while changing policy eligibility. A clause stating that a handler accepted requests cannot imply end-to-end recovery unless service probes establish it separately.

The selected definition belongs in a new version of the report questions and prewritten report annotations. A matched comparison can then freeze that change before scoring further development families. Specialist review and new held-out families remain necessary before operational evaluation. The current 140 packets and replay texts are inspected development evidence.

No existing input, reference or score should be rewritten to make the model's answer correct. If a reviewer changes an earlier reference, record a separate version and separately identified re-score alongside the original result.

[The study guide](report-language.md) records the controls, exact input boundaries, measured scores and immutable run locations.
