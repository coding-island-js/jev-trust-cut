# 2026-10-02: one cut per side, not one symmetric cut

**Decision:** compute the "Jev says yes" cut and the "Jev says no" cut separately.

**Why:** the first version mirrored one number around 0.5 (p >= 0.73 or p <= 0.27). On EatList only the yes side had checked rows, so the "no" half of that answer had no evidence at all. When the one confident "no" was checked (Rancho Cucamonga, p = 0.37), Jev was wrong, so that side gets no cut.

**Changes:** [the cut](../concepts/the-cut.md).
