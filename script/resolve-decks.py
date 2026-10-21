#!/usr/bin/env python3
"""Give every card in decks/ an oracle_id, its Scryfall name, and its original printing.

Decklists are copied in the way their source printed them: "Delver of Secrets"
for a double-faced card, a Japanese name from mtg-jp.com, an old spelling from
1996. The oracle_id is what makes them the same card, so it is what a count of
"most played" adds up, and what a deck is checked against the restricted list
by -- the state files key their cards the same way.

The source's spelling stays in `printed_as` when it differs, so a list can
always be compared back to where it came from.

Everything is answered from Scryfall's `default_cards` bulk file -- every
printing, downloaded once into .cache/ and reused until Scryfall publishes a
newer one -- so a run makes one request to check for that, not one per card.

    python3 script/resolve-decks.py              # report only
    python3 script/resolve-decks.py --write      # also fill the files in
    python3 script/resolve-decks.py --offline    # use the cached file as is

Lookups go by `name`. Cards that match nothing are listed and left alone; put
the English name in `name`, the source's spelling in `printed_as` (a Japanese
name, say), and run it again.
"""
import argparse, datetime, glob, gzip, io, json, os, re, sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECKS = os.path.join(REPO, "decks")
CACHE = os.path.join(REPO, ".cache", "scryfall")
UA = {"User-Agent": "type1-decks-resolve/1.0", "Accept": "application/json"}
# not cards a deck can play, but they share names with ones that are
NOT_CARDS = {"token", "double_faced_token", "emblem", "art_series", "vanguard",
             "scheme", "planar"}


def bulk_file(offline):
    """Path to the newest default_cards file, downloading it if Scryfall has a newer one."""
    have = sorted(glob.glob(os.path.join(CACHE, "default-cards-*.jsonl.gz")))
    if offline:
        if not have:
            sys.exit("no cached default_cards file; run once without --offline")
        return have[-1]
    req = urllib.request.Request("https://api.scryfall.com/bulk-data/default-cards", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        uri = json.load(r)["jsonl_download_uri"]
    path = os.path.join(CACHE, os.path.basename(uri))
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        print(f"downloading {uri}", file=sys.stderr)
        with urllib.request.urlopen(urllib.request.Request(uri, headers=UA), timeout=600) as r, \
                open(path + ".part", "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        os.replace(path + ".part", path)
        for old in have:
            os.remove(old)
    return path


def legal_paper(p):
    """The printings the state files count: paper, and never excluded from the
    tournament pool (pool_exclusions: Collectors' and International Edition,
    silver border and acorn, digital)."""
    return ("paper" in p.get("games", []) and p["set_type"] not in ("memorabilia", "funny")
            and p.get("border_color") != "silver" and p.get("security_stamp") != "acorn")


# frame treatments that make a printing a variant of the card, not the card.
# "legendary" and the like are part of the card's own frame.
VARIANT_FRAMES = {"showcase", "extendedart", "inverted", "etched", "borderless",
                  "shatteredglass", "fullart"}
# promo_types that say nothing about the printing being special
PLAIN_PROMO_TYPES = {"universesbeyond"}


def plain(p):
    """The card as its set printed it for the booster: not a promo, in English,
    and not a showcase, borderless, serialized or other alternate version.

    Release date alone picks wrong. New Phyrexia's prerelease promos are dated
    2011-05-12, a day before the set, so Phyrexian Metamorph came out as a
    datestamped 42★; and among The One Ring's same-day LTR printings the
    lowest collector number is 0, the serialized 1-of-1 in Elvish.
    """
    return (not p.get("promo") and p["set_type"] != "promo"
            and p.get("lang", "en") == "en"
            and not p.get("variation")
            and not (p.get("full_art") and "Basic Land" not in p.get("type_line", ""))
            and p.get("border_color") != "borderless"
            and not set(p.get("frame_effects") or []) & VARIANT_FRAMES
            and not set(p.get("promo_types") or []) - PLAIN_PROMO_TYPES)


def days_between(a, b):
    return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days


def collector_key(n):
    m = re.match(r"(\d+)(.*)", n)
    return (int(m.group(1)), m.group(2)) if m else (1 << 30, n)


def load(path):
    """name -> oracle_id, and oracle_id -> its original printing."""
    names, faces, first, first_plain = {}, {}, {}, {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            oid = p.get("oracle_id")
            if not oid or p["layout"] in NOT_CARDS:
                continue
            names[p["name"]] = oid
            for face in p.get("card_faces", []):
                faces.setdefault(face["name"], set()).add(oid)
            if legal_paper(p):
                key = (p["released_at"], p["set"], collector_key(p["collector_number"]))
                if oid not in first or key < first[oid][0]:
                    first[oid] = (key, p)
                if plain(p) and (oid not in first_plain or key < first_plain[oid][0]):
                    first_plain[oid] = (key, p)
    # "Delver of Secrets" for "Delver of Secrets // Insectile Aberration", where
    # the face names only one card
    for n, oids in faces.items():
        if n not in names and len(oids) == 1:
            names[n] = next(iter(oids))
    # The plain printing is the original when it follows the earliest one
    # within a year: that earliest one was a promo for it -- a prerelease, a
    # release-day foil, an FNM or judge card whose date Scryfall only knows to
    # the year. A promo that came long before any plain printing is the
    # original in its own right: Mana Crypt was a 1995 book insert, 21 years
    # before Eternal Masters.
    out = {}
    for oid, (key, p) in first.items():
        pl = first_plain.get(oid)
        out[oid] = pl[1] if pl and days_between(key[0], pl[0][0]) <= 365 else p
    return names, out


def printing(p):
    image = (p.get("image_uris") or p["card_faces"][0]["image_uris"])["normal"]
    return {"set": p["set"].upper(), "set_name": p["set_name"],
            "released_at": p["released_at"], "collector_number": p["collector_number"],
            "rarity": p["rarity"], "image": image, "scryfall_uri": p["scryfall_uri"]}


def cards_of(doc):
    for deck in doc["decks"]:
        for part in ("main", "sideboard"):
            yield from deck.get(part) or []  # null: the list is lost


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    names, first = load(bulk_file(args.offline))

    unmatched, changed = set(), set()
    for fn in sorted(os.listdir(DECKS)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(DECKS, fn)
        doc = json.load(io.open(path, encoding="utf-8"))
        before = json.dumps(doc, sort_keys=True)
        for c in cards_of(doc):
            oid = names.get(c["name"])
            if oid is None or oid not in first:
                unmatched.add((fn, c["name"]))
                continue
            p = first[oid]
            if p["name"] != c["name"]:
                c.setdefault("printed_as", c["name"])
                c["name"] = p["name"]
            c["oracle_id"] = oid
            c["original_printing"] = printing(p)
        if json.dumps(doc, sort_keys=True) != before:
            changed.add(fn)
            if args.write:
                with io.open(path, "w", encoding="utf-8") as f:
                    json.dump(doc, f, indent=1, ensure_ascii=False)
                    f.write("\n")

    print(f"{len(changed)} files {'updated' if args.write else 'would change'}, "
          f"{len(unmatched)} unmatched")
    for fn, n in sorted(unmatched):
        print(f"  {fn}: {n}")
    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
