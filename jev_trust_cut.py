"""jev-trust-cut: find how sure Jev has to be before you act on its answer.

You already have a decision for every row (a rule, a person, an old model).
Jev answers the same yes/no question for each row with a probability.
Where they disagree, a person decides who was right. The cut is the lowest
probability where Jev was still right on the rows a person checked.

    python jev_trust_cut.py score  rows.jsonl --question "..."   # calls Jev once per row
    python jev_trust_cut.py report rows.scored.jsonl              # band table + review sheet
    # fill the "truth" column in rows.review.csv (1 = yes, 0 = no), then:
    python jev_trust_cut.py report rows.scored.jsonl --review rows.review.csv

Input rows are JSON lines: {"id": "...", "text": "...", "label": 0 or 1}.
No dependencies. Needs TYPESAFE_API_KEY in the environment.
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
PRICE_PER_INPUT_TOKEN = 42 / 1e9  # $42 per billion input tokens; output is free
BANDS = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0001]


def read_rows(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def ask(row, question, key):
    body = json.dumps({
        "state": row["text"],
        "model": MODEL,
        "questions": {"q": {"type": "noul", "instructions": question}},
    }).encode("utf-8")
    request = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            return {**row, "p": round(payload["answers"]["q"]["noul"], 3),
                    "input_tokens": payload.get("usage", {}).get("input_tokens", 0)}
        except urllib.error.HTTPError as error:
            if error.code < 500:  # bad key or bad request: retrying will not help
                return {**row, "p": None, "error": f"HTTP {error.code}"}
            if attempt == 2:
                return {**row, "p": None, "error": f"HTTP {error.code}"}
        except (urllib.error.URLError, OSError, KeyError, ValueError) as error:
            if attempt == 2:
                return {**row, "p": None, "error": str(error)[:200]}
        time.sleep(2 ** attempt)
    return {**row, "p": None, "error": "unreachable"}


def score(args):
    key = os.environ.get("TYPESAFE_API_KEY") or sys.exit("Set TYPESAFE_API_KEY first.")
    rows = read_rows(args.rows)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        scored = list(pool.map(lambda r: ask(r, args.question, key), rows))
    out = Path(args.rows).with_suffix(".scored.jsonl")
    write_rows(out, scored)
    tokens = sum(r.get("input_tokens", 0) for r in scored)
    errors = sum(1 for r in scored if r["p"] is None)
    print(f"scored {len(scored) - errors} rows, {errors} errors, {tokens:,} input tokens, "
          f"about ${tokens * PRICE_PER_INPUT_TOKEN:.4f}")
    print(f"wrote {out}")


def band_of(p):
    for low, high in zip(BANDS, BANDS[1:]):
        if low <= p < high:
            return f"{low:.1f}-{min(high, 1.0):.1f}"


def report(args):
    rows = [r for r in read_rows(args.scored) if r.get("p") is not None]
    truth = {}
    if args.review:
        with open(args.review, encoding="utf-8") as handle:
            for line in csv.DictReader(handle):
                if line["truth"].strip() in ("0", "1"):
                    truth[line["id"]] = int(line["truth"])

    print(f"\n{len(rows)} rows. Jev says yes when p >= 0.5.\n")
    print(f"{'Jev p':<9}{'rows':>6}{'agree':>8}{'disagree':>10}{'checked':>9}{'Jev right':>11}")
    disagreements = []
    for low, high in zip(BANDS, BANDS[1:]):
        band = [r for r in rows if low <= r["p"] < high]
        if not band:
            continue
        split = [r for r in band if (r["p"] >= 0.5) != bool(r["label"])]
        disagreements += split
        checked = [r for r in split if r["id"] in truth]
        right = sum(1 for r in checked if (r["p"] >= 0.5) == bool(truth[r["id"]]))
        verdict = f"{right}/{len(checked)}" if checked else "-"
        print(f"{band_of(low):<9}{len(band):>6}{len(band) - len(split):>8}{len(split):>10}"
              f"{len(checked):>9}{verdict:>11}")

    if not args.review:
        sheet = Path(args.scored).with_name(Path(args.scored).name.replace(".scored.jsonl", ".review.csv"))
        with open(sheet, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "p", "your_label", "truth", "text"])
            for r in sorted(disagreements, key=lambda r: -abs(r["p"] - 0.5)):
                writer.writerow([r["id"], r["p"], r["label"], "", r["text"].replace("\n", " | ")])
        print(f"\n{len(disagreements)} disagreements written to {sheet}.")
        print("Put the real answer in the truth column (1 = yes, 0 = no), then run report with --review.")
        return

    # The cut, one per side: walk the checked disagreements from Jev's most
    # confident inward and stop at the first one Jev got wrong.
    print()
    for side, says_yes in (("yes", True), ("no", False)):
        checked = sorted((r for r in disagreements if r["id"] in truth and (r["p"] >= 0.5) == says_yes),
                         key=lambda r: abs(r["p"] - 0.5), reverse=True)
        if not checked:
            print(f"Jev says {side}: nothing checked yet, so no cut. Keep your current decision.")
            continue
        cut = None
        for r in checked:
            if says_yes != bool(truth[r["id"]]):
                break
            cut = r["p"]
        if cut is None:
            print(f"Jev says {side}: wrong on its most confident disagreement. Do not act on it alone.")
        else:
            sign = ">=" if says_yes else "<="
            print(f"Jev says {side}: trust it over your current decision when p {sign} {cut:.2f}, "
                  f"right on {sum(1 for r in checked if abs(r['p'] - 0.5) >= abs(cut - 0.5))} checked.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(required=True)
    s = sub.add_parser("score", help="ask Jev about every row")
    s.add_argument("rows")
    s.add_argument("--question", required=True, help="a yes/no statement Jev rates as a probability")
    s.add_argument("--workers", type=int, default=8)
    s.set_defaults(func=score)
    r = sub.add_parser("report", help="band table, review sheet, and the cut")
    r.add_argument("scored")
    r.add_argument("--review", help="the review CSV with the truth column filled in")
    r.set_defaults(func=report)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
