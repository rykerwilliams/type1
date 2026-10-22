# decks/

Top 8 decklists from the Type 1 / Vintage championships, one file per event,
named `YYYY-MM-DD-slug.json` so they sort by date.

Each deck is dated, so it can be read against the restricted list in force on
the day it was played: the last `archive/` state whose `effective` is on or
before the event's `date`.

## Which events

Every event that was, at the time, the championship for Type 1 / Vintage:

- **before 2003**: no recurring official championship. 1994 Worlds (played
  under what became Type 1), the AndCon Type I championships in Toledo, the
  1996 Pro Tour Dallas Classic, and the 2000 Beyond Dominia Tournament of
  Champions. Most of their lists are lost; these are kept partial.
- **2003–2012**: the Vintage Championship at Gen Con (2008: U.S. Nationals,
  Chicago).
- **2013 on**: Eternal Weekend North America, plus Europe (from 2016) and
  Asia (from 2018). 2020 and 2021 were six events on Magic Online.

Top 8 only, even where the cut was larger.

## File

```json
{
 "event": "2013 Vintage Championship",
 "label": "Eternal Weekend NA",
 "date": "2013-11-03",
 "location": "Philadelphia, PA",
 "players": 232,
 "source": {"url": "...", "archived": "...", "label": "Wizards event coverage"},
 "partial": false,
 "notes": [],
 "decks": [
  {
   "finish": "1",
   "seed": 6,
   "player": "Joel Lim",
   "archetype": "Reel Fish",
   "main": [{"count": 4, "name": "Lord of Atlantis"}],
   "sideboard": [{"count": 2, "name": "Energy Flux"}]
  }
 ]
}
```

| field | |
|---|---|
| `event` | the name it had at the time |
| `label` | short name shown with it: `Gen Con`, `Eternal Weekend NA`, `Eternal Weekend Europe`, `Eternal Weekend Asia`, `Eternal Weekend Online` … |
| `date` | the day the Top 8 was played. Where that is not known, a placeholder: the last day of what is known, so the restricted list it selects is the latest the event could have used |
| `date_precision` | absent when `date` is the real day; otherwise `range` (with `date_range: [first, last]`), `month` or `year`. Show the range, month or year, never the placeholder day |
| `players` | `null` if unknown; where sources disagree, the primary source's figure, with the others in `notes` |
| `source` | where the lists were copied from. `archived` is a Wayback copy when the original is gone or may go |
| `partial` | `true` when fewer than eight full lists are known |
| `notes` | `[{"text": ..., "url": ...}]`, for anything a reader comparing sources would trip over |
| `decks[].finish` | `"1"`, `"2"`, `"3-4"`, `"5-8"`, or `"1"`…`"8"` where the event placed every slot |
| `decks[].seed` | Swiss standing going into the Top 8, `null` if unknown |
| `decks[].player` | in English; `player_native` alongside where the source wrote it otherwise (`十文字 諒`). One person has one name across every file: where sources spell the same player differently (Steve and Stephen, Demars and DeMars), use the spelling most of their Top 8 sources give, and add a deck `notes` entry with the source's own spelling |
| `decks[].archetype` | MTGGoldfish's name where Goldfish has the event, for consistency across events; otherwise as the source named it. Where Goldfish gives only a colour code (`WUR`, `Colorless`), the source's name is kept and the event's notes say so |
| `decks[].source` | only where this deck came from somewhere other than the event's `source` |
| `decks[].main`, `sideboard` | `null` when the list is not known. A known list with no sideboard printed keeps `"sideboard": null` and says so in `notes` |
| `decks[].notes` | as for the event |

Cards carry `name` (English, as Scryfall spells it), and the source's own
spelling in `printed_as` where that differs. `script/resolve-decks.py --write`
adds `oracle_id` and `original_printing` to every card.

## Copying a list

1. Copy from the original coverage. A list that exists in no original source
   may come from the `lhc` sets on Deckbox, with `decks[].source` saying so.
2. Copy what the source printed. Where it is plainly wrong (a card listed
   twice, a 61st card, two of a restricted card), fix it from a second source
   and leave a note naming both.
3. Placings come from the playoff itself: official coverage, the organizer's
   bracket, match reports. Never from a site's ordering of the Top 8 alone:
   mtgtop8 often lists it by Swiss standing, which named the wrong champion
   for 2022 NA. On Melee, read the playoff rounds' match results, not the
   final standings, which have the order wrong for 2023 NA and Europe.

`python3 script/check-decks.py` checks every file.
