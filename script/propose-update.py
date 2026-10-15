#!/usr/bin/env python3
"""Draft the event for a B&R change that Scryfall has and this repo does not.

Scryfall publishes no B&R history: only each card's CURRENT legality, with no
date and no announcement. So a divergence tells us WHAT changed but not WHEN,
and inventing a date is the one thing this dataset must not do.

The date is therefore DISCOVERED, not guessed. Wizards' announcement URLs are
predictable and, more usefully, verifiable -- a real one returns 200 and an
invented one returns 404:

    .../news/announcements/banned-and-restricted-august-10-2026
    .../news/announcements/august-26-2024-banned-and-restricted-announcement

So this walks back over recent Mondays, asks for each candidate URL, and uses
the first that exists. If none does, the draft is written with null dates and
says so, rather than filling them in with a plausible lie.

    python3 script/propose-update.py            # report only
    python3 script/propose-update.py --write    # also write events.json
"""
import argparse, datetime as dt, io, json, os, re, sys
import urllib.error, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "type1-br-propose/1.0", "Accept": "application/json"}
HTML_UA = {"User-Agent": "Mozilla/5.0 (compatible; type1-br-propose/1.0)"}
BASE = "https://magic.wizards.com/en/news/announcements/"
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify import replay, scryfall                      # noqa: E402


def live_legality():
    """name -> 'restricted' | 'banned', from Scryfall.

    Detection keys off the RESTRICTED list only. Scryfall's banned list for
    Vintage is 101 cards, nearly all of them acorn, digital or Conspiracy
    cards that this repository holds as class rules rather than replaying as
    events -- comparing against it proposed 82 bans that had not happened.
    The banned side is only consulted to tell WHY a card left the restricted
    list: banned, or legal again.
    """
    out = {n: "restricted" for n in scryfall("restricted")}
    for n in scryfall("banned"):
        out.setdefault(n, "banned")
    return out


def candidate_urls(day):
    m, d, y = MONTHS[day.month - 1], day.day, day.year
    return [f"{BASE}banned-and-restricted-{m}-{d}-{y}",
            f"{BASE}{m}-{d}-{y}-banned-and-restricted-announcement"]


def acts_on(url, cards):
    """Does this announcement act on one of these cards IN VINTAGE?

    Every announcement carries a per-format summary:

        ... Legacy The Fantasticar is banned.
            Vintage The Fantasticar is restricted.
            Pauper No changes ...

    and a quiet one reads "Vintage No changes". Merely finding the card name
    somewhere on the page is not enough -- the October 2026 announcement
    discusses The Fantasticar at length while changing nothing in Vintage, and
    a name-only test picked it as the source of the August restriction. So
    only the Vintage section counts.
    """
    try:
        req = urllib.request.Request(url, headers=HTML_UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
    except Exception:
        return False
    import html as _html
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"\s+", " ", t)
    m = re.search(r"\bVintage\b(.{0,400}?)\b(?:Pauper|Alchemy|Historic|Timeless|Brawl)\b",
                  t, re.I | re.S)
    if not m:
        return False
    section = m.group(1)
    if re.search(r"no changes", section, re.I):
        return False
    return any(c.lower() in section.lower() for c in cards)


def find_announcement(cards, since_days=400):
    """The announcement that actually made this change.

    Taking the most recent announcement that exists is not good enough: run
    against a repository that has fallen behind, it returned the October 2026
    announcement for a change made in August 2026. So each candidate page is
    fetched and kept only if it NAMES one of the changed cards. An
    announcement that does not mention the card did not make the change.
    """
    today = dt.date.today()
    for back in range(0, since_days):
        day = today - dt.timedelta(days=back)
        if day.weekday() != 0:          # announcements land on Mondays
            continue
        for url in candidate_urls(day):
            try:
                req = urllib.request.Request(url, headers=HTML_UA, method="HEAD")
                with urllib.request.urlopen(req, timeout=25) as r:
                    if r.status != 200:
                        continue
            except Exception:
                continue
            if not acts_on(url, cards):
                continue                 # exists, but is not about this change
            return {"date": day.isoformat(), "url": url,
                    "label": (f"Banned & Restricted Announcement "
                              f"{MONTHS[day.month-1].title()} "
                              f"{day.day}, {day.year}")}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="append the drafted event to events.json")
    args = ap.parse_args()

    doc = json.load(io.open(os.path.join(REPO, "events.json")))
    events = doc["events"]
    rep_r, rep_b, _ = replay(events)
    live = live_legality()

    live_r = {n for n, k in live.items() if k == "restricted"}
    actions = []
    for name in sorted(live_r - rep_r):
        actions.append({"card": name, "action": "restrict"})
    for name in sorted(rep_r - live_r):
        # it left the restricted list: banned now, or legal again?
        actions.append({"card": name,
                        "action": "ban" if live.get(name) == "banned"
                        else "unrestrict"})
    # Deliberately NOT scanning Scryfall's banned list for new entries: it is
    # full of cards that were never legal here. A brand-new ban of a card this
    # repository has never tracked will not be caught automatically, and the
    # issue text says so.

    if not actions:
        print("no difference: nothing to propose")
        return 0

    ann = find_announcement([a["card"] for a in actions])
    seq = max(e["seq"] for e in events) + 1
    draft = {
        "seq": seq,
        "date": ann["date"] if ann else None,
        "date_precision": "day" if ann else None,
        "effective": ann["date"] if ann else None,
        "announced": ann["date"] if ann else None,
        "era": None,
        "era_name": None,
        "announcement": ({"url": ann["url"], "label": ann["label"]}
                         if ann else None),
        "actions": [dict(a, resolved_from="scryfall") for a in actions],
        "sources": ["https://scryfall.com"] + ([ann["url"]] if ann else []),
        "NEEDS_REVIEW": (
            "Drafted automatically from a Scryfall divergence. "
            + ("The announcement was found by probing Wizards' URLs and "
               "confirmed to name the card. Its date is the ANNOUNCEMENT "
               "date; confirm the EFFECTIVE date, which is often later."
               if ann else
               "No announcement page was found, so the dates are null and "
               "must be filled in by hand. Do not guess them.")),
    }

    print(f"{len(actions)} change(s) Scryfall has that this repo does not:")
    for a in actions:
        print(f"   {a['action']:11} {a['card']}")
    print()
    print("announcement: " + (ann["url"] if ann else "NOT FOUND -- dates left null"))
    print()
    print(json.dumps(draft, indent=1))

    if args.write:
        doc["events"] = events + [draft]
        io.open(os.path.join(REPO, "events.json"), "w").write(
            json.dumps(doc, indent=1) + "\n")
        print("\nappended to events.json -- current.json and archive/ still "
              "need rebuilding, and the dates still need a human")
    return 0


if __name__ == "__main__":
    sys.exit(main())
