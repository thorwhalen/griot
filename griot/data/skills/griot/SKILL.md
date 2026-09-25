---
name: griot
description: >
  Research a subject and write the spoken commentary script about it, with a
  reusable writer (general, technical, song) — the step BEFORE a braidio
  production is voiced. Use when someone wants a script written from a topic:
  "write a commentary about <song/book/film/idea>", "research X and draft the
  narration", "what would this cost to write and voice", "give me a dossier on
  X", "which writer should do this", "add a writer". Free, tokenless research
  (Wikipedia, Genius, LRCLIB) into a sourced dossier; one priced, cached LLM
  call into a gated braidio.Script plus a picture hint per beat. Not for
  voicing (braidio), pictures (illustration) or the film (braidio-commentary-video).
---

# griot

A griot knows the record and performs it. This package does the two halves that come *before* braidio: **research** a topic into evidence, then **write** the commentary from that evidence with a named, reusable writer.

```bash
pip install griot            # braidio + falaw + httpx + bs4
python -m griot writers      # the three shipped writers
```

## Shortest path

```python
import griot

w = griot.get_writer("song")                                   # general | technical | song
dossier = griot.research("The Sound of Silence by Simon & Garfunkel", researchers=w.researchers)
q = griot.quote(w, dossier, minutes=3)      # priced BEFORE anything runs: q.total_usd, q.has_unknown_costs
draft = griot.write(w, dossier, minutes=3)  # one LLM call (+ at most one gated revision), content-cached
draft.script            # a braidio.Script — hand it to braidio.weave_project / render_format
draft.picture_hints     # one per beat: query, subject label, why — the picture track's provenance
draft.report            # the gates' findings; empty when it passed
draft.ok                # False means: read the report, do not voice it yet
```

CLI: `python -m griot quote "<topic>" --writer song --minutes 3`, `python -m griot write "<topic>" --writer general --out draft.json`, and `--fake` to run the whole path with no key and no spend.

## What a writer is

A `Writer` is **data**: a brief (how it writes and what it looks for), a braidio `format_id` whose `scripting` guidance it inherits, 2–4 critic voices it *blends* from the style library (never impersonates one), the researchers it sends out first, a word budget, a gate list, a model. The three shipped ones are `griot/data/writers/*.md` — front matter plus the brief. Another writer is one Markdown file, or `register_writer(Writer(...))` in process.

| writer | for | researchers | voices blended |
|---|---|---|---|
| `general` | any subject — a book, a film, a place, a person, an idea | wikipedia | Barbaro, Longworth, Bragg |
| `technical` | how a mechanism, method or result works | wikipedia | McWhorter, Bragg, Hirway |
| `song` | one song: what it says, how it is built, the recording's story | genius, wikipedia, lrclib | Sloan & Harding, Caramanica, Hirway, Rubin |

The prompt every writer assembles: its brief → the voice cards → the anti-platitude checklist → the format's scripting guidance → the house rules → the job (minutes, word budget, angle) → the dossier as a flat evidence brief → a strict JSON contract. The house rules are the ones real episodes were sent back for: ≤2 designed epigrams per 3 minutes; 2–5 varied `[audio tags]` per 100 words; documented fact to a second "record" voice; lyrics only as brief attributed fragments; never impersonate; every claim from the dossier or say it is unknown.

## Research

`research(topic, researchers=(...))` runs named fetchers in order and merges. Each fact carries its source URL; what could not be found goes under `missing`, and the writer is *told* — it never substitutes the nearest match ("Actually Sweet" does not resolve to "Actually Romantic").

- **wikipedia** — search, summary, lead extract. Write a song as `"<song> by <artist>"`; the artist disambiguates the album from the song.
- **genius** — song search, lyrics, per-line annotations. Set `GENIUS_ACCESS_TOKEN` (a Client Access Token from genius.com/api-clients) to use the official API. **Without it, the tokenless public API is refused by Cloudflare as of 2026-09-25** and the researcher records the miss; annotations are then unavailable.
- **lrclib** — synced lyric timings *and* plain lyrics, so a song still has its lyric sheet when Genius is blocked. Needs `<song> by <artist>` or a prior resolution.

A researcher that fails (a 403, a timeout) is recorded under `missing`; the others still run.

## The gates, and what to do when a draft fails

`draft.report.findings` names each failure in words the writer acts on, and `write` sends them back for one bounded revision by default (`Writer.max_revisions`). A draft that still fails is **returned with its report**, `draft.ok == False`. Read it: `platitudes` (braidio's tic audit), `expressiveness` (tag density band), `lyric_leak` (a whole lyric line verbatim), `length` (±30% of the budget the price was quoted on), `shape` (≥3 beats, a picture hint per beat). Voicing an `ok == False` draft is a choice, not an accident.

## Cost

`quote()` composes the same falaw plan `write()` would run, so `llm_usd` is the plan's own ceiling × (1 + revisions), and `tts_usd` is braidio's TTS rate on the word budget. An unpriced model gives `llm_unknown=True` and `has_unknown_costs=True` — **unknown is never zero**; gate on the flag. The LLM call is content-cached by falaw: the same writer, dossier and minutes never bill twice.

## Seams

- `write(..., complete=fn)` — any `(plan) -> (reply_text, cost_usd)`; tests and dry runs use it. `Writer.model` — any fal any-llm id in falaw's rate table.
- `research(..., http=obj)` — anything with `.json(url, params=, headers=)` / `.text(...)`; tests use an in-memory fake.
- `register_researcher(name)` / `register_writer(Writer)` — more sources, more writers.

## Where this stops

griot hands over a `braidio.Script` and picture hints. Voicing is **braidio** (`weave_project`, `render_format`); finding the pictures is **illustration**; the film over them is the **braidio-commentary-video** skill; the studio flow that runs all of it is **reelee** (`commentary.create`).
