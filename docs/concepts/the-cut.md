# The cut

The cut is the confidence above which Jev's answer should beat the existing decision.

How `report --review` finds it, separately for each side (Jev says yes, Jev says no):

1. Take the disagreements on that side that a person checked.
2. Sort them from Jev's most confident to its least confident (distance from 0.5).
3. Walk down the list. Stop at the first one Jev got wrong.
4. The cut is the last probability where Jev was still right.

If Jev's most confident checked answer was already wrong, there is no cut for that side. The existing decision stays in charge.

If nothing on a side was checked, there is no cut either.

Known limit: ties. If a wrong row has exactly the same p as the cut, it counts inside the trusted range.

Decisions: [2026-10-02 per-side cut](../decisions/2026-10-02-per-side-cut.md).
