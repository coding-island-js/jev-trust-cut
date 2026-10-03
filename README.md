# jev-trust-cut

**How sure does Jev have to be before you act on its answer? This tool finds that number on your own data.**

[Jev](https://typesafe.ai) answers a yes/no question with a probability. The obvious move is to act when it says more than 0.5. On my data, where Jev disagreed with my rules between 0.5 and 0.7, it was wrong on every row I checked. And its most confident disagreements found real bugs my rules had missed.

So the number that matters is not 0.5. It is the point above which Jev keeps being right, and you can only find that by checking it against decisions you already have.

## What it does

1. **You bring rows you have already decided.** A rule, a person, or an old model said yes or no for each one.
2. **`score` asks Jev the same question for every row.** One call per row, run in parallel. It costs a fraction of a cent per few hundred rows.
3. **`report` shows where Jev disagrees with you, grouped by how sure it was.** It writes the disagreements to a sheet, with the most confident ones at the top.
4. **A person fills in the real answer for the rows they can check.**
5. **`report --review` gives you the cut.** It walks from Jev's most confident disagreement inward and stops at the first one Jev got wrong. The cut is the last one it got right. Below it, keep your current decision.

```bash
export TYPESAFE_API_KEY=...
python jev_trust_cut.py score  rows.jsonl --question "This video was filmed outside Los Angeles."
python jev_trust_cut.py report rows.scored.jsonl
# fill the truth column in rows.review.csv, then:
python jev_trust_cut.py report rows.scored.jsonl --review rows.review.csv
```

Each input row is one JSON line: `{"id": "...", "text": "...", "label": 0 or 1}`. The tool has no dependencies beyond Python 3.10.

## The real example: EatList

[EatList](https://eatlist.withmagic.ai) builds a map of LA restaurants from food YouTubers' videos. A rule-based gate decides whether each video was filmed in LA or Orange County. If the gate gets that wrong, a restaurant from another city shows up on an LA map.

Every row in `examples/eatlist/` is real. The data is 482 public video titles, plus what the gate did with each one. Label 0 means the video published LA places. Label 1 means the gate skipped it as out of market. The question Jev was asked:

> This video was filmed OUTSIDE Los Angeles County and Orange County, California. Treat a video as outside only if the food shown was eaten somewhere else. A dish named after another place (Nashville hot chicken, Chicago deep dish, Philly cheesesteak, New York pizza) does NOT mean the video was filmed there.

```
Jev p      rows   agree  disagree  checked  Jev right
0.0-0.1      82      82         0        0          -
0.1-0.3      75      75         0        0          -
0.3-0.5     151     150         1        1        0/1
0.5-0.7     149       4       145        3        0/3
0.7-0.9       9       2         7        4        3/4
0.9-1.0      16      12         4        4        4/4

Jev says yes: trust it over your current decision when p >= 0.73, right on 7 checked.
Jev says no: wrong on its most confident disagreement. Do not act on it alone.
```

**At 0.5, Jev would have thrown out 145 videos the gate kept.** Almost all of them come from an LA channel and have titles like "Jollibee" or "Porto's Cubano" that name no place. Jev isn't sure about those, and it says so by staying near 0.5. That's honest, but you can't act on it.

**At 0.73 and up, Jev was right on all 7 rows I checked, and each one was a real bug in the gate.** Videos from Egypt, New York's Chinatown, Louisiana, San Diego (twice), Santa Maria and the Inland Empire had published restaurants onto the LA map. The first wrong answer was Whittier at 0.70, which is in LA County. That's what sets the cut.

**The no side has no cut.** The one confident "no" that was checked was Rancho Cucamonga, and Rancho Cucamonga really is outside LA and Orange County, so Jev was wrong. The gate stays in charge there.

All 482 rows cost **$0.0072** in Jev calls. An earlier run on September 18, 2026 (data not in this repo) showed the same pattern. On 150 unseen titles, Jev was right every time at 0.9 and up, and wrong 12 times out of 12 between 0.5 and 0.7.

## How to use the result

- Use Jev as an auditor, not a step in your pipeline. Run it over decisions you have already made, and send the confident disagreements to a person.
- Find your own cut. The 0.73 here comes from this data and this question. Yours will be different.
- Checked rows are the only evidence. In this example, 12 rows were checked by reading the title, and only where the title names the place. The rest are left blank on purpose.
- Seven checks above the cut is a small sample, and they are the easy rows. Three unchecked rows above 0.73 ("South African Lunch", "Japanese Street Food", "NY Water + Everything Bagel") come from an LA channel and are probably Jev mistakes. Treat the cut as a starting point, and check more rows before you rely on it.

## License

MIT
