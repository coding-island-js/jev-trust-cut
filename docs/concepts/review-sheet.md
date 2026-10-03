# The review sheet

`report` without `--review` writes `<name>.review.csv`: every disagreement between Jev and the existing decision, most confident first.

Columns: `id`, `p` (Jev's probability for yes), `your_label` (the existing decision), `truth` (blank, for a person), `text`.

A person fills `truth` with 1 or 0 only for rows they can actually verify. Blank means unchecked, and that is fine. The cut uses checked rows only.

Running `report` again without `--review` overwrites the sheet, including any truth already filled in.

Decisions: [2026-10-02 checked rows only](../decisions/2026-10-02-checked-rows-only.md).
