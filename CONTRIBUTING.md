# Contributing

This repository is only as good as its citations, and it was built by people
who weren't at most of these events. If something here is wrong, or cited to
the wrong place, or you know where a lost list lives, please say so.

Corrections are the contribution that matters most. A wrong card count, a
misspelled name or a dead link is worth an issue.

## The easy way: open an issue

[Open an issue](https://github.com/rykerwilliams/type1/issues/new) with three
things:

1. **what** is wrong: the file, or just the event and player, or the
   announcement date;
2. **what** it should be;
3. **where** that comes from: a link, a scan, a magazine and page number.

The third one is the important one. Every fact here points at a source, so a
fix needs one too. If you are the source — it was your deck, or you were in
that Top 8 — say so; that counts, and the note on the fix will record it.

No need to know JSON, git or the file format. An issue is enough, and someone
will make the change.

## What's wanted

**Lost lists.** These events are missing decks, standings or both. Any of them
is welcome: a list, a photo of a decklist, the standings.

| event | players known | of those, list lost |
|---|---|---|
| 1994 Worlds | 4 of 8 | 2 |
| 1995 AndCon | 2 | 2 |
| 1996 AndCon | 1 | 1 |
| 1996 Pro Tour Dallas | 8 | 5 |
| 1997 AndCon | 1 | |
| 1998 AndCon | none | |
| 2000 Beyond Dominia | 1 | |

**Open questions** from the original import, each noted in its file:

- **2007 Gen Con**: who lost the semifinal to Richard Shay? The other five
  quarterfinalists are all listed 5–8 until that's known.
- **2017 and 2018 NA, 2025 Europe**: places below the final rest on mtgtop8
  alone. Official standings or coverage would settle them.
- **2022–2025 NA**: lists not yet compared against Melee.
- **2018 Asia**: one romanized name, Uesugi, is uncertain.

**Better sources.** A list copied from a secondary site (mtgtop8, the lhc
sets on Deckbox, a forum repost) should point at its original coverage when that can
be found, even if the list doesn't change.

**Other major tournaments.** `decks/` holds the championships only, but Top 8s
from other major Vintage events are of interest too: the big paper opens,
invitationals, Vintage at the old Grand Prix and SCG events. They have no home
yet, so [open an issue](https://github.com/rykerwilliams/type1/issues/new)
rather than a pull request: name the event, link the coverage the lists come
from, and they'll get a folder of their own, in the same format, once the
first ones arrive. Sources are not optional here either: a Top 8 with no
coverage to point at won't go in.

## Sending a pull request

### Decklists

The format and the copying rules are in [`decks/README.md`](decks/README.md).
The short version:

- Copy what the source printed. Put the card's English name in `name`; if the
  source spelled it differently (a Japanese name, an old spelling), keep that
  in `printed_as`.
- Where a source is plainly wrong, fix it from a second source and add a
  `notes` entry naming both. Don't silently change a list.
- Placings come from the official coverage or the organizer, never from a site
  that sorts the Top 8 by Swiss record.

Then:

```
python3 script/resolve-decks.py --write   # fills in oracle_id and original printing
python3 script/check-decks.py             # deck sizes, restricted cards, structure
```

Both must pass. `resolve-decks.py` downloads Scryfall's bulk card data once
(about 80 MB) into `.cache/`, and lists any name it can't match.

### The B&R history

An issue is the better route here. `events.json` is the record, but every
snapshot in `archive/` and `current.json` is a replay of it, and changing one
event means rebuilding every snapshot after it. If you do send a change to
`events.json`, cite the announcement — ideally the original, with an archived
copy — and say so in the PR; it will be replayed and rechecked before merging.

```
python3 script/verify.py
```

checks the replay, the snapshots, and today's list against Scryfall.

## What won't be merged

- **A change with no source.** Even a correct one: the next person can't tell
  it from a mistake.
- **A counterfactual.** This records what the list was and what was played,
  not what should have been. Menendian's *Schools of Magic* is deliberately
  not a source for that reason.
- **A Top 8 that isn't the championship, in `decks/`.** Other major events are
  welcome, but in their own folder: see *Other major tournaments* above.
