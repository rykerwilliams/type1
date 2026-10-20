#!/usr/bin/env python3
"""Check every file in decks/ against the rules in decks/README.md.

    python3 script/check-decks.py               # all files
    python3 script/check-decks.py decks/x.json  # just these

Structure, deck sizes, and -- once resolve-decks.py has given the cards their
oracle_ids -- the restricted list in force on the event's date: a deck with
two of a restricted card was copied wrong. Non-zero exit on any error.
"""
import io, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINISHES = {"1", "2", "3-4", "5-8"} | {str(i) for i in range(3, 9)}


def states():
    out = []
    adir = os.path.join(REPO, "archive")
    for fn in sorted(os.listdir(adir)):
        if fn.endswith(".json"):
            st = json.load(io.open(os.path.join(adir, fn), encoding="utf-8"))
            out.append((st["effective"], {c["oracle_id"] for c in st["restricted"]}))
    return out


def in_force(date, sts):
    r = None
    for eff, ids in sts:
        if eff <= date:
            r = ids
    return r


def check(path, sts):
    errs = []
    fn = os.path.basename(path)
    d = json.load(io.open(path, encoding="utf-8"))
    for k in ("event", "label", "date", "source", "decks"):
        if k not in d:
            errs.append(f"missing {k}")
    if errs:
        return errs
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", d["date"]) or not fn.startswith(d["date"]):
        errs.append(f"date {d['date']} does not match file name")
    prec = d.get("date_precision")
    if prec not in (None, "range", "month", "year"):
        errs.append(f"date_precision {prec!r}")
    if prec == "range":
        r = d.get("date_range") or []
        if len(r) != 2 or not r[0] <= d["date"] == r[1]:
            errs.append(f"date_range {r} must end on the placeholder date")
    if len(d["decks"]) > 8:
        errs.append(f"{len(d['decks'])} decks; Top 8 only")
    full = sum(1 for x in d["decks"] if x.get("main") is not None and x.get("sideboard") is not None)
    if full < 8 and not d.get("partial"):
        errs.append(f"only {full} full lists but not marked partial")
    restricted = in_force(d["date"], sts)
    for x in d["decks"]:
        who = x.get("player", "?")
        if x.get("finish") not in FINISHES:
            errs.append(f"{who}: finish {x.get('finish')!r}")
        if x.get("main") is None:
            continue
        n = sum(c["count"] for c in x["main"])
        if n < 60:
            errs.append(f"{who}: main deck {n} cards")
        side = x.get("sideboard") or []
        s = sum(c["count"] for c in side)
        if s > 15:
            errs.append(f"{who}: sideboard {s} cards")
        # a short sideboard is allowed only when a note says the source printed it so
        if x.get("sideboard") is not None and s < 15 and not x.get("notes"):
            errs.append(f"{who}: sideboard {s} cards, with no note")
        seen = {}
        for c in x["main"] + side:
            key = c.get("oracle_id") or c["name"]
            seen[key] = seen.get(key, 0) + c["count"]
            if restricted and c.get("oracle_id") in restricted and seen[key] > 1:
                errs.append(f"{who}: {seen[key]} of restricted {c['name']}")
        dup = [c["name"] for c in x["main"] if [m["name"] for m in x["main"]].count(c["name"]) > 1]
        if dup:
            errs.append(f"{who}: listed twice in main: {sorted(set(dup))}")
    return errs


def main():
    paths = sys.argv[1:] or [os.path.join(REPO, "decks", f)
                             for f in sorted(os.listdir(os.path.join(REPO, "decks")))
                             if f.endswith(".json")]
    sts = states()
    bad = 0
    for p in paths:
        errs = check(p, sts)
        bad += bool(errs)
        print(("FAIL " if errs else "ok   ") + os.path.basename(p))
        for e in errs:
            print("     " + e)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
