#!/usr/bin/env python3
"""Prove the B&R data.

Four checks:

1. `current.json` equals a replay of `events.json`.
2. every snapshot in `archive/` equals a replay up to its own sequence number.
3. no orphaned or no-op actions. An unrestriction with no prior restriction is
   an orphan; restricting an already-restricted card is a no-op. Both mean an
   event is missing.
4. the replay reproduces Scryfall's live Vintage list exactly.

Check 3 matters because checks 1, 2 and 4 cannot see a missing PAIR of events:
the two cancel out and the final list still comes out right. That is how Ivory
Tower, Mirror Universe, Recall, Underworld Dreams, Stroke of Genius, Regrowth
and the 1994 Shahrazad ban were all missing while the end-state check passed.
The no-op half of the check catches the rest: Time Vault's 1994 ban and 1996
unban were both absent, and the only trace was that its 2008 restriction
restricted a card that was already restricted.

    python3 script/verify.py

Non-zero exit on any discrepancy, so this works as a CI gate.
"""
import io, json, os, sys, urllib.parse, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "type1-br-verify/1.0", "Accept": "application/json"}


def scryfall(kind):
    url = ("https://api.scryfall.com/cards/search?q="
           + urllib.parse.quote(f"{kind}:vintage")
           + "&unique=cards&order=name")
    names = set()
    while url:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=60) as r:
            d = json.load(r)
        names |= {c["name"] for c in d.get("data", [])}
        url = d.get("next_page")
    return names


def replay(events, audit=False):
    """Replay the events. With audit=True, also collect two kinds of flaw.

    ORPHAN: an undo with nothing to undo -- unrestricting a card that was not
    restricted. Means the matching action is missing.

    NO-OP: an action that changes nothing -- restricting a card that is already
    restricted. A real announcement never does that, so it means an intervening
    event is missing. This is the only signal for a missing PAIR: a lost
    ban+unban cancels out, so neither the end-state check nor the orphan check
    can see it. Time Vault's 1994 ban and 1996 unban were both missing, and
    only the no-op on its 2008 restriction gave them away.
    """
    ORDER = {"unban": 0, "unrestrict": 1, "ban": 2, "restrict": 3}
    restricted, banned, flaws = set(), set(), []
    for e in sorted(events, key=lambda e: e["seq"]):
        # An announcement's actions are SIMULTANEOUS. "Channel and Mind Twist
        # unbanned" and their restriction are one act, so each action is
        # judged against the state BEFORE the announcement; judging it against
        # a state that a sibling action already changed raises false alarms.
        # Removals are applied before additions.
        pre_r, pre_b = set(restricted), set(banned)
        for a in sorted(e["actions"], key=lambda a: ORDER.get(a["action"], 9)):
            c, act = a["card"], a["action"]
            if audit:
                if act == "restrict" and c in pre_r:
                    flaws.append((e["date"], c, "no-op: already restricted"))
                elif act == "unrestrict" and c not in pre_r:
                    flaws.append((e["date"], c, "orphan: was not restricted"))
                elif act == "ban" and c in pre_b:
                    flaws.append((e["date"], c, "no-op: already banned"))
                elif act == "unban" and c not in pre_b:
                    flaws.append((e["date"], c, "orphan: was not banned"))
            if act == "restrict":
                restricted.add(c); banned.discard(c)
            elif act == "unrestrict":
                restricted.discard(c)
            elif act == "ban":
                banned.add(c); restricted.discard(c)
            elif act == "unban":
                banned.discard(c)
    return restricted, banned, flaws


def main():
    doc = json.load(io.open(os.path.join(REPO, "events.json")))
    events = doc["events"] if isinstance(doc, dict) else doc
    cur = json.load(io.open(os.path.join(REPO, "current.json")))
    rep_r, rep_b, flaws = replay(events, audit=True)
    cur_r = {c["name"] for c in cur["restricted"]}
    bad = 0

    if rep_r != cur_r:
        bad += 1
        print("FAIL current.json disagrees with replaying events.json")
        for c in sorted(cur_r - rep_r): print("   only in current.json:", c)
        for c in sorted(rep_r - cur_r): print("   only in replay      :", c)
    else:
        print(f"ok   current.json matches the replay ({len(cur_r)} restricted)")

    adir = os.path.join(REPO, "archive")
    n = 0
    for fn in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        if not fn.endswith(".json"):
            continue
        st = json.load(io.open(os.path.join(adir, fn)))
        want, _, _ = replay([e for e in events if e["seq"] <= st["sequence"]])
        got = {c["name"] for c in st["restricted"]}
        if want != got:
            bad += 1
            print(f"FAIL archive/{fn}: {sorted(got ^ want)[:6]}")
        n += 1
    print(f"ok   {n} archived snapshots each match a replay to their sequence")

    if flaws:
        bad += 1
        print(f"FAIL {len(flaws)} action(s) imply a hole in the history")
        for d, c, why in flaws:
            print(f"   {d:12} {c:26} {why}")
    else:
        print("ok   no orphaned or no-op actions; every action changes state")

    try:
        sky = scryfall("restricted")
    except Exception as exc:                       # offline is not a failure
        print(f"skip Scryfall check ({exc})")
        return bad
    miss, extra = sorted(sky - rep_r), sorted(rep_r - sky)
    if miss or extra:
        bad += 1
        print("FAIL against Scryfall's live list:")
        for c in miss:  print("   restricted today, not produced by replay:", c)
        for c in extra: print("   replay restricts, Scryfall does not     :", c)
    else:
        print(f"ok   replay reproduces Scryfall's live list exactly "
              f"({len(sky)} restricted)")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
