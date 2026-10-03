# AGENTS.md

One Python file, no dependencies. It asks Jev (TypeSafe's yes/no model) about rows that already have a decision, then finds how sure Jev must be before its answer should override that decision.

## Commands

- Score rows (calls the paid API, about $0.007 per 500 rows): `TYPESAFE_API_KEY=... python jev_trust_cut.py score rows.jsonl --question "..."`
- Band table and review sheet (no API call): `python jev_trust_cut.py report rows.scored.jsonl`
- The cut, after a person fills the truth column: `python jev_trust_cut.py report rows.scored.jsonl --review rows.review.csv`
- Check the example still reproduces (no API call): `PYTHONIOENCODING=utf-8 python jev_trust_cut.py report examples/eatlist/titles.scored.jsonl --review examples/eatlist/titles.review.csv`
  The last two lines must read `p >= 0.73, right on 7 checked` and `wrong on its most confident disagreement`.

## Layout

- `jev_trust_cut.py`: everything. `score`, `report`, and the cut logic at the bottom of `report`.
- `examples/eatlist/`: real data. `titles.scored.jsonl` is the frozen input for the README numbers.
- `docs/concepts/`: how things work now, one idea per file.
- `docs/decisions/`: why, one dated file per decision, never edited.

## Things that look right and are wrong

- **Never re-run `score` on the example.** It costs money and Jev's answers can shift, which would break every number in the README. Work from `titles.scored.jsonl`.
- **"Wrong" is about the checked rows, not all rows.** Most disagreements are unchecked on purpose. Do not fill the truth column with guesses.
- **The cut is per side.** A "yes" cut says nothing about "no" answers. See `docs/concepts/the-cut.md`.
- **`label` is what the existing rule did**, not the truth. In the example, 1 means the gate skipped the video as out of market.
- **Keep it dependency-free.** Standard library only, Python 3.10+.
- **Windows consoles need `PYTHONIOENCODING=utf-8`** for the example's emoji titles.
