# type1

A versioned list of the Banned & Restricted list for Type 1 (Vintage).

> ### Built on Steve Menendian's work
>
> Nearly everything here derives from
> **[Timeline of Vintage](https://www.eternalcentral.com/timeline-of-vintage/)**
> by **Steve Menendian**, at Eternal Central. His era chart records what
> changed, when it took effect, when it was announced, and where to find the
> announcement. The dates, the era names and the citations in this repository
> are his research. This repository only replays them into a state you can
> read off for a given day.
>
> Go and read the original — it carries the reasoning behind every decision,
> which is the part no dataset replaces.
>
> Only facts are taken from it: dates, card names, era names and links. The
> article's prose is not reproduced here.

## Why this exists

Published B&R sources list the **changes** — this card restricted, that one
unrestricted. None list the **state** on a given day. Answering "what was
legal in spring 1999?" means replaying every announcement from 1994 forward
and hoping you missed none.

This repository is that replay, done once and checked:

- **`current.json`** — the list as it stands now.
- **`archive/NNNN-YYYY-MM-DD.json`** — the same state after every
  announcement, under a name that sorts chronologically and parses both ways.
- **`events.json`** — the announcements, append-only.
- **`eras.json`** — all 171 rows of the era chart.
- **one commit per announcement**, backdated to it, so the commit history *is*
  the timeline.

```
git log --date=short --format='%ad %s'      # the timeline
git show <sha>:current.json                 # the list on that date
git log -p --follow current.json            # every change, in order
```

## The whole chart, not just the bans

Not every change to the format is a B&R action. Errata move it with no
announcement at all — Time Vault was errata'd into uselessness in 1996 and
errata'd back in 2008, which is why its 2008 restriction exists — and so do
rules changes and set releases. `eras.json` keeps all of it, each era tagged
with what drove it:

| kind | eras |
|---|---|
| `set_release` | 93 |
| `banned_restricted` | 48 |
| `rules` | 13 |
| `errata` | 11 |
| `format` | 7 |

271 notable printings across 93 eras.

## Announcement date vs effective date

These are not the same, and a tournament held between them used the **old**
list. The chart gives both: an era ends when a change takes effect, and its
citation names the announcement, which is usually earlier — Fact or Fiction
was announced on 1 December 2001 and took effect on 1 January 2002. Events are
dated by their **effective** date and carry `announced` alongside. All 49
announcements are day-precise.

## What is in a state file

Each snapshot carries the restricted cards with enough context to be useful
without a second lookup: type line, mana cost, oracle id, rulings endpoint,
and the **original paper printing** — set, code, release date, collector
number, rarity and image. Original, not whichever printing Scryfall returns by
default: a Vintage list should show Black Lotus as Alpha.

It also carries the banned cards and the **class bans**. Ante and the seven
cards removed in June 2020 for offensive content name a definite set of cards,
so they are replayed as ordinary ban events — 19 banned cards in all — with
the rule kept alongside to say why. Conspiracy and stickers stay rule-only,
having no finite named list here.

Separately, `pool_exclusions` records printings that were never tournament
legal at all: Collectors' and International Edition (1993-12-10), Astral Cards
(1997-04-01), Unglued onward (1998-08-11). These are not bans — no B&R action
ever applied to them — and each is dated to the first set of its kind, because
the exclusion means nothing before that.

## Verification

```
python3 script/verify.py
```

Four checks:

1. `current.json` equals a replay of `events.json`.
2. every snapshot in `archive/` equals a replay up to its own sequence.
3. **no orphaned or no-op actions.** An unrestriction with no prior
   restriction is an *orphan*; restricting an already-restricted card is a
   *no-op*. Both mean an event is missing.
4. the replay reproduces **Scryfall's live Vintage list** exactly.

All four pass: **52 restricted**, 19 banned. Non-zero exit otherwise, so it
works as a CI gate.

Check 3 earns its place, because the others cannot see a missing **pair** of
events — the two cancel out and the final list still comes out right. Ivory
Tower, Mirror Universe, Recall, Underworld Dreams, Stroke of Genius, Regrowth
and Shahrazad's 1994 ban were all absent while end-state verification passed
clean. The no-op half catches the rest: Time Vault's 1994 ban and 1996 unban
were *both* missing, and the only trace was that its 2008 restriction
restricted a card the data already had as restricted.

An announcement's actions are treated as **simultaneous** — "Channel and Mind
Twist unbanned" and their restriction are one act — so each action is judged
against the state before the announcement, not against a state a sibling
action already changed.

## Sources

| | |
|---|---|
| [Timeline of Vintage](https://www.eternalcentral.com/timeline-of-vintage/) | Steve Menendian, Eternal Central. The era chart this is built from. |
| [MTG Wiki B&R timeline](https://mtg.fandom.com/wiki/Banned_and_restricted_cards/Timeline) | Used only where the chart does not enumerate a change: the first list, and the 18 cards of September 1999. |
| [WotC announcements](https://magic.wizards.com/en/news/announcements) | The primary source each citation points at, and for 2025 onward. |
| [Scryfall](https://scryfall.com) | Card identity, original printings, and the live list the replay is checked against. |

Citations carry an archived copy where the Wayback Machine has one, 34 of 53.
Several cited sources are a tripod.com page, a Google Groups post and a
crystalkeep mirror, none of which will outlast the format.

Menendian's
[Schools of Magic](https://www.eternalcentral.com/history-of-vintage-schools-of-magic-an-alternative-history-of-the-banned-and-restricted-list/)
is deliberately **not** a source. It is an *alternative* history: it argues
what should have been restricted, not what was. Mixing it in would blend the
real list with a counterfactual one.
